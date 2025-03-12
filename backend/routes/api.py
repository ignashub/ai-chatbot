from flask import Blueprint, request, jsonify, current_app
import sys
import os
import tempfile
import json
from datetime import datetime
import time
from functools import wraps
import threading
import re

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.moderation import is_prompt_safe
from services.ai_service import generate_ai_response
from services.function_calling import get_all_reminders, search_nutrition, set_reminder
from services.knowledge_base import search_knowledge_base, KNOWLEDGE_BASE_DIR, vector_store, get_embedding
from services.document_loader import load_document_from_url, load_document_from_file, list_documents

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Global variable to store processing logs
document_processing_logs = []
# Dictionary to track request counts for rate limiting
request_counts = {}
# Lock for thread-safe operations
request_lock = threading.Lock()

# Rate limiting decorator
def rate_limit(limit=20, window=60):
    """
    Rate limiting decorator that allows a maximum of 'limit' requests per 'window' seconds
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            with request_lock:
                # Clean up old entries
                for ip in list(request_counts.keys()):
                    request_counts[ip] = [t for t in request_counts.get(ip, []) if current_time - t < window]
                
                # Check if client has exceeded rate limit
                if len(request_counts.get(client_ip, [])) >= limit:
                    # For logs endpoint, return the last known logs instead of an error
                    if request.path == '/documents/logs':
                        return jsonify({
                            "logs": document_processing_logs,
                            "rate_limited": True,
                            "retry_after": window - (current_time - min(request_counts.get(client_ip, [current_time]))) if request_counts.get(client_ip) else 0
                        }), 429
                    else:
                        return jsonify({
                            "error": "Rate limit exceeded. Please try again later.",
                            "retry_after": window - (current_time - min(request_counts.get(client_ip, [current_time]))) if request_counts.get(client_ip) else 0
                        }), 429
                
                # Add current request timestamp
                if client_ip not in request_counts:
                    request_counts[client_ip] = []
                request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def add_processing_log(message):
    """Add a message to the processing logs."""
    global document_processing_logs
    timestamp = datetime.now().isoformat()
    document_processing_logs.append({"timestamp": timestamp, "message": message})
    # Keep only the last 100 log entries
    if len(document_processing_logs) > 100:
        document_processing_logs = document_processing_logs[-100:]
    print(message)  # Also print to console

# Chat endpoint
@api_bp.route('/chat', methods=['OPTIONS', 'POST'])
def chat():
    """
    Chat endpoint that handles user messages and returns AI responses.
    
    Returns:
        JSON: Response containing AI message and metadata
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.json
        user_message = data.get('message', '')
        system_prompt = data.get('systemPrompt', "You are a Health and Wellness Coach. You can help set reminders for health activities and provide nutrition information for food items.")
        model = data.get('model', "gpt-4")  # Allow model selection
        temperature = data.get('temperature', 0.7)
        top_p = data.get('topP', 1.0)
        frequency_penalty = data.get('frequencyPenalty', 0.0)
        presence_penalty = data.get('presencePenalty', 0.0)

        # Ensure user_message is not None
        if user_message is None:
            return jsonify({'error': 'Message cannot be null'}), 400

        # Check if message is safe
        is_safe, reason = is_prompt_safe(user_message)
        if not is_safe:
            return jsonify({'error': reason}), 403
            
        # Check if the query is about a specific document
        document_specific = False
        document_context = ""
        
        # Look for document references in the query
        if '.pdf' in user_message.lower() or 'document' in user_message.lower():
            document_specific = True
            print(f"Document-specific query detected: {user_message}")
            
            # Extract potential document name from query
            potential_docs = re.findall(r'([a-zA-Z0-9_-]+\.pdf)', user_message)
            
            # If document names found, search for them specifically
            if potential_docs:
                print(f"Document names found in query: {potential_docs}")
                
                # Create a more specific query that includes the document name
                enhanced_query = user_message
                for doc_name in potential_docs:
                    enhanced_query += f" {doc_name}"
                
                # Check if the query is asking about a specific section
                section_query = False
                potential_sections = re.findall(r'([A-Z][a-z]+(?:\s+[a-z]+)*)', user_message)
                for section in potential_sections:
                    if len(section.split()) > 1:  # Only consider multi-word phrases as potential sections
                        enhanced_query += f" {section}"
                        section_query = True
                
                # Get document context
                query_embedding = get_embedding(enhanced_query)
                
                # Increase top_k for document-specific queries to get more context
                top_k_value = 20 if section_query else 15
                
                print(f"Using enhanced query: {enhanced_query} with top_k={top_k_value}")
                results = vector_store.search(query_embedding, top_k=top_k_value)
                
                if results:
                    document_context = "Here is information from the documents you asked about:\n\n"
                    
                    # Group results by document title for better organization
                    docs_by_title = {}
                    for doc in results:
                        title = doc.get('title', 'Unknown')
                        if title not in docs_by_title:
                            docs_by_title[title] = []
                        docs_by_title[title].append(doc)
                    
                    # Add content from each document
                    for title, docs in docs_by_title.items():
                        document_context += f"--- From document: {title} ---\n\n"
                        
                        # Sort chunks by their position in the document if possible
                        try:
                            docs = sorted(docs, key=lambda x: int(x.get('id', '0').split('-')[-1]) if x.get('id', '0').split('-')[-1].isdigit() else 0)
                        except:
                            pass  # If sorting fails, use the original order
                        
                        # Combine content from all chunks
                        combined_content = ""
                        for doc in docs:
                            content = doc.get('content', 'No content available')
                            # Clean up content if needed
                            content = re.sub(r'([a-z])([A-Z])', r'\1 \2', content)
                            
                            # Check if this chunk contains a section header that matches the query
                            section_headers = re.findall(r'([A-Z][a-z]+(?:\s+[a-z]+)*)', content)
                            for header in section_headers:
                                if header.lower() in user_message.lower():
                                    # Highlight this section as particularly relevant
                                    content = f"RELEVANT SECTION - {header}:\n{content}"
                                    break
                            
                            combined_content += f"{content}\n\n"
                        
                        # Add the combined content
                        document_context += combined_content
                    
                    print(f"Found {len(results)} relevant document chunks from {len(docs_by_title)} documents")
                else:
                    document_context = "I couldn't find any relevant information in the documents you mentioned."
                    print("No relevant documents found")
                
                # Enhance system prompt for document queries with more specific instructions
                system_prompt += "\nWhen answering about documents, focus on the specific information provided in the context below and include ALL relevant details from the documents. If asked about specific sections or content from a document, provide a comprehensive and detailed response that includes ALL key points, tools, methods, and examples mentioned in that section. Do not omit important details or examples. Pay special attention to sections marked as 'RELEVANT SECTION' as they directly relate to the user's query. Be sure to include ALL specific tools, measurements, and frameworks mentioned in these sections."
            else:
                # If no specific document name found, do a general search
                query_embedding = get_embedding(user_message)
                results = vector_store.search(query_embedding, top_k=8)
                
                if results:
                    document_context = "Here is some relevant information from our document collection:\n\n"
                    for i, doc in enumerate(results):
                        doc_title = doc.get('title', 'Unknown')
                        doc_content = doc.get('content', 'No content available')
                        # Clean up content if needed
                        doc_content = re.sub(r'([a-z])([A-Z])', r'\1 \2', doc_content)
                        document_context += f"Document {i+1} from {doc_title}:\n{doc_content}\n\n"
                    
                    print(f"Found {len(results)} relevant document chunks for general query")

        # Generate AI response
        full_message = user_message
        if document_context:
            full_message = document_context + "\n\nUser query: " + user_message
            print(f"Added document context ({len(document_context)} chars) to user message")
        
        response_text, input_tokens, output_tokens, estimated_cost = generate_ai_response(
            user_message=full_message,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )

        return jsonify({
            'response': response_text,
            'tokens': {
                'input': input_tokens,
                'output': output_tokens,
                'total': input_tokens + output_tokens
            },
            'estimated_cost': f"${estimated_cost}"
        })
    except Exception as e:
        import traceback
        print(f"Error in chat endpoint: {e}")
        print(traceback.format_exc())
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

# Reminders endpoints
@api_bp.route('/reminders', methods=['GET'])
def get_reminders():
    """
    Get all reminders.
    
    Returns:
        JSON: List of all reminders
    """
    return jsonify(get_all_reminders())

@api_bp.route('/reminders', methods=['POST'])
def create_reminder():
    """
    Create a new reminder directly.
    
    Returns:
        JSON: Created reminder
    """
    data = request.json
    title = data.get('title')
    date = data.get('date')
    time = data.get('time')
    description = data.get('description')
    
    if not all([title, date, time]):
        return jsonify({'error': 'Title, date, and time are required'}), 400
    
    result = set_reminder(title, date, time, description)
    
    if result.get('success'):
        return jsonify(result), 201
    else:
        return jsonify(result), 400

# Nutrition endpoints
@api_bp.route('/nutrition', methods=['GET'])
def get_nutrition():
    """
    Search for nutrition information about a food item using query parameters.
    
    Returns:
        JSON: Nutrition information
    """
    food_item = request.args.get('food_item')
    quantity = request.args.get('quantity', 100)
    unit = request.args.get('unit', 'g')
    
    if not food_item:
        return jsonify({'error': 'Food item is required'}), 400
    
    try:
        quantity = float(quantity)
    except ValueError:
        return jsonify({'error': 'Quantity must be a number'}), 400
    
    result = search_nutrition(food_item, quantity, unit)
    return jsonify(result)

@api_bp.route('/nutrition', methods=['POST'])
def search_nutrition_info():
    """
    Search for nutrition information about a food item using JSON body.
    
    Returns:
        JSON: Nutrition information
    """
    data = request.json
    food_item = data.get('food_item')
    quantity = data.get('quantity', 100)
    unit = data.get('unit', 'g')
    
    if not food_item:
        return jsonify({'error': 'Food item is required'}), 400
    
    result = search_nutrition(food_item, quantity, unit)
    return jsonify(result)

# Knowledge base endpoint
@api_bp.route('/knowledge', methods=['GET', 'POST'])
def knowledge():
    """
    Search the knowledge base for relevant information.
    
    Returns:
        JSON: Relevant knowledge base entries
    """
    if request.method == 'GET':
        query = request.args.get('query')
    else:  # POST
        data = request.json
        query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    # Check if query is safe
    is_safe, reason = is_prompt_safe(query)
    if not is_safe:
        return jsonify({'error': reason}), 403
    
    # Search the knowledge base
    results = search_knowledge_base(query)
    
    return jsonify({
        'query': query,
        'results': results
    })

# Document management endpoints
@api_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all documents in the knowledge base."""
    try:
        # Get the knowledge base directory
        kb_dir = KNOWLEDGE_BASE_DIR
        
        if not os.path.exists(kb_dir):
            return jsonify({"documents": [], "count": 0})
        
        documents = []
        
        # Iterate through subdirectories (each represents a document)
        for doc_dir in os.listdir(kb_dir):
            doc_path = os.path.join(kb_dir, doc_dir)
            
            # Skip if not a directory
            if not os.path.isdir(doc_path):
                continue
                
            # Try to read metadata
            metadata_path = os.path.join(doc_path, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        documents.append({
                            "id": doc_dir,
                            "title": metadata.get("title", "Untitled Document"),
                            "source": metadata.get("source", "Unknown"),
                            "date_added": metadata.get("date_added", "Unknown")
                        })
                except Exception as e:
                    print(f"Error reading metadata for {doc_dir}: {str(e)}")
            else:
                # If no metadata, just use the directory name
                documents.append({
                    "id": doc_dir,
                    "title": f"Document {doc_dir}",
                    "source": "Unknown",
                    "date_added": "Unknown"
                })
        
        return jsonify({"documents": documents, "count": len(documents)})
    except Exception as e:
        print(f"Error listing documents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/documents/logs', methods=['GET'])
@rate_limit(limit=10, window=10)  # Increased to 10 requests per 10 seconds
def get_processing_logs():
    """Get document processing logs"""
    # Add a small artificial delay to prevent rapid successive requests
    time.sleep(0.05)
    return jsonify({"logs": document_processing_logs})

@api_bp.route('/documents/url', methods=['POST'])
def add_document_from_url():
    """
    Add a document from a URL to the knowledge base.
    
    Returns:
        JSON: Added document
    """
    try:
        # Clear previous logs
        global document_processing_logs
        document_processing_logs = []
        
        data = request.json
        url = data.get('url')
        
        if not url:
            add_processing_log("Error: URL is required")
            return jsonify({'error': 'URL is required', 'logs': document_processing_logs}), 400
        
        add_processing_log(f"Processing document from URL: {url}")
        
        # Check if URL is safe
        is_safe, reason = is_prompt_safe(url)
        if not is_safe:
            add_processing_log(f"URL failed safety check: {reason}")
            return jsonify({'error': reason, 'logs': document_processing_logs}), 403
        
        # Load document from URL with progress updates
        add_processing_log(f"Starting document download from {url}")
        
        # Set a longer timeout for the request to prevent server crashes
        # This is a potentially long-running operation
        try:
            documents = load_document_from_url(url)
        except Exception as e:
            add_processing_log(f"Error during document processing: {str(e)}")
            import traceback
            add_processing_log(traceback.format_exc())
            add_processing_log(f"Failed to process document from {url}")
            return jsonify({
                'error': f'Error processing document: {str(e)}',
                'logs': document_processing_logs
            }), 500
        
        if not documents:
            add_processing_log(f"No documents were extracted from {url}")
            return jsonify({
                'error': 'Failed to extract content from the URL. The document might be in an unsupported format or protected.',
                'logs': document_processing_logs
            }), 400
        
        add_processing_log(f"Successfully processed {len(documents)} chunks from {url}")
        return jsonify({
            'message': f'Added {len(documents)} document chunks from URL',
            'document_count': len(documents),
            'url': url,
            'logs': document_processing_logs
        }), 201
    except Exception as e:
        add_processing_log(f"Error processing document from URL: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        add_processing_log(traceback_str)
        add_processing_log(f"Failed to process document from {url}")
        return jsonify({
            'error': f'Error processing document: {str(e)}',
            'logs': document_processing_logs
        }), 500

@api_bp.route('/documents/file', methods=['POST'])
def add_document_from_file():
    """
    Add a document from a file to the knowledge base.
    
    Returns:
        JSON: Added document
    """
    try:
        # Clear previous logs
        global document_processing_logs
        document_processing_logs = []
        
        add_processing_log("Starting file upload processing")
        
        if 'file' not in request.files:
            add_processing_log("Error: No file part in the request")
            return jsonify({'error': 'No file part in the request', 'logs': document_processing_logs}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            add_processing_log("Error: No file selected")
            return jsonify({'error': 'No file selected', 'logs': document_processing_logs}), 400
        
        # Get file extension
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else None
        
        if file_extension not in ['pdf', 'txt']:
            add_processing_log(f"Error: Unsupported file extension: {file_extension}")
            return jsonify({'error': f'Unsupported file extension: {file_extension}', 'logs': document_processing_logs}), 400
        
        add_processing_log(f"Processing file: {file.filename}, type: {file.content_type}")
        
        # Save file content
        file_content = file.read()
        add_processing_log(f"File size: {len(file_content)} bytes")
        
        # Check if file is safe
        is_safe, reason = is_prompt_safe(file.filename)
        if not is_safe:
            add_processing_log(f"File failed safety check: {reason}")
            return jsonify({'error': reason, 'logs': document_processing_logs}), 403
        
        # Process file with progress updates
        try:
            add_processing_log(f"Starting document processing for {file.filename}")
            documents = load_document_from_file(file.filename, file_content, file_extension)
        except Exception as e:
            add_processing_log(f"Error during document processing: {str(e)}")
            import traceback
            add_processing_log(traceback.format_exc())
            add_processing_log(f"Failed to process document from file: {file.filename}")
            return jsonify({
                'error': f'Error processing document: {str(e)}',
                'logs': document_processing_logs
            }), 500
        
        if not documents:
            add_processing_log(f"No documents were extracted from {file.filename}")
            return jsonify({
                'error': 'Failed to extract content from the file. The document might be in an unsupported format or protected.',
                'logs': document_processing_logs
            }), 400
        
        add_processing_log(f"Successfully processed {len(documents)} chunks from {file.filename}")
        return jsonify({
            'message': f'Added {len(documents)} document chunks from file',
            'document_count': len(documents),
            'filename': file.filename,
            'logs': document_processing_logs
        }), 201
    except Exception as e:
        add_processing_log(f"Error processing document from file: {str(e)}")
        import traceback
        traceback_str = traceback.format_exc()
        add_processing_log(traceback_str)
        add_processing_log("Document processing failed")
        return jsonify({
            'error': f'Error processing document: {str(e)}',
            'logs': document_processing_logs
        }), 500

@api_bp.route('/documents/debug', methods=['GET'])
def debug_documents():
    """
    Get all documents in the vector store for debugging.
    
    Returns:
        JSON: List of all documents in the vector store
    """
    documents = []
    for doc in vector_store.documents:
        # Include only essential information to avoid large responses
        documents.append({
            "title": doc.get("title", "Unknown"),
            "content_preview": doc.get("content", "")[:100] + "..." if len(doc.get("content", "")) > 100 else doc.get("content", ""),
            "source": doc.get("source", "Unknown"),
            "id": doc.get("id", "Unknown")
        })
    
    return jsonify({
        "document_count": len(documents),
        "documents": documents
    }) 

@api_bp.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """
    Delete a document from the knowledge base.
    
    Args:
        doc_id: The document ID to delete
        
    Returns:
        JSON: Success message
    """
    try:
        # Path to the document directory
        doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, doc_id)
        
        if not os.path.exists(doc_dir):
            return jsonify({'error': f'Document with ID {doc_id} not found'}), 404
        
        # Get document metadata
        metadata_file = os.path.join(doc_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                title = metadata.get("title", "Unknown document")
        else:
            title = "Unknown document"
        
        # Remove document chunks from vector store
        # We need to find the indices of documents with this ID prefix
        indices_to_remove = []
        for i, doc in enumerate(vector_store.documents):
            if "id" in doc and doc["id"].startswith(doc_id):
                indices_to_remove.append(i)
        
        # Remove from vector store (in reverse order to avoid index shifting)
        for index in sorted(indices_to_remove, reverse=True):
            vector_store.documents.pop(index)
            vector_store.embeddings.pop(index)
        
        # Delete the document directory
        import shutil
        shutil.rmtree(doc_dir)
        
        return jsonify({
            'success': True,
            'message': f'Document "{title}" deleted successfully',
            'deleted_chunks': len(indices_to_remove)
        })
    except Exception as e:
        print(f"Error deleting document: {str(e)}")
        return jsonify({'error': f'Error deleting document: {str(e)}'}), 500

@api_bp.route('/search', methods=['POST'])
def search():
    """
    Search for documents in the knowledge base.
    
    Returns:
        JSON: Search results
    """
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 4)  # Default to 4 documents
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Check if the query is about a specific document
        document_specific = False
        if '.pdf' in query.lower() or 'document' in query.lower():
            document_specific = True
            # Extract potential document name from query
            potential_docs = re.findall(r'([a-zA-Z0-9_-]+\.pdf)', query)
            if potential_docs:
                # Boost the query with the document name to improve retrieval
                query = f"{query} {' '.join(potential_docs)}"
        
        # Get embedding for the query
        query_embedding = get_embedding(query)
        
        # Search for similar documents
        results = vector_store.search(query_embedding, top_k=top_k)
        
        # Enhance results with more context
        documents = []
        for result in results:
            # Check if result has the expected structure
            if 'document' in result:
                doc = result['document']
            else:
                # If the result is already a document (not wrapped in a 'document' field)
                doc = result
                print(f"Document found: {doc.get('title', 'Unknown')} (id: {doc.get('id', 'Unknown')})")
            
            # Make a copy to avoid modifying the original
            doc_copy = doc.copy() if isinstance(doc, dict) else {'content': str(doc)}
            
            # Try to get surrounding chunks for more context if this is a document-specific query
            if document_specific and isinstance(doc, dict) and 'id' in doc:
                try:
                    doc_id_parts = doc['id'].split('-')
                    if len(doc_id_parts) > 1:
                        base_id = doc_id_parts[0]
                        chunk_index = int(doc_id_parts[1])
                        
                        # Try to get previous and next chunks
                        prev_id = f"{base_id}-{chunk_index-1}"
                        next_id = f"{base_id}-{chunk_index+1}"
                        
                        prev_doc = vector_store.get_document(prev_id)
                        next_doc = vector_store.get_document(next_id)
                        
                        # Add content from previous chunk if available
                        if prev_doc and 'content' in prev_doc:
                            doc_copy['content'] = prev_doc['content'] + "\n\n" + doc_copy.get('content', '')
                        
                        # Add content from next chunk if available
                        if next_doc and 'content' in next_doc:
                            doc_copy['content'] = doc_copy.get('content', '') + "\n\n" + next_doc['content']
                except Exception as e:
                    print(f"Error enhancing document context: {e}")
                    # Continue with the original document if there's an error
            
            # Clean up content if needed - add spaces between words that are run together
            if 'content' in doc_copy and isinstance(doc_copy['content'], str):
                # Fix common OCR issues where words are run together
                doc_copy['content'] = re.sub(r'([a-z])([A-Z])', r'\1 \2', doc_copy['content'])
            
            documents.append(doc_copy)
        
        # If no documents were found, return an empty list
        if not documents:
            print(f"No documents found for query: {query}")
            return jsonify({
                'documents': [],
                'query': query,
                'message': 'No relevant documents found'
            })
        
        return jsonify({
            'documents': documents,
            'query': query
        })
    except Exception as e:
        import traceback
        print(f"Error in search endpoint: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'documents': []}), 500