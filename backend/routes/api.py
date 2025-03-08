from flask import Blueprint, request, jsonify
import sys
import os
import tempfile

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.moderation import is_prompt_safe
from services.ai_service import generate_ai_response
from services.function_calling import get_all_reminders, search_nutrition, set_reminder
from services.knowledge_base import search_knowledge_base, KNOWLEDGE_BASE_DIR
from services.document_loader import load_document_from_url, load_document_from_file, list_documents

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__)

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

    data = request.json
    user_message = data.get('message')
    system_prompt = data.get('systemPrompt', "You are a Health and Wellness Coach. You can help set reminders for health activities and provide nutrition information for food items.")
    model = data.get('model', "gpt-4")  # Allow model selection
    temperature = data.get('temperature', 0.7)
    top_p = data.get('topP', 1.0)
    frequency_penalty = data.get('frequencyPenalty', 0.0)
    presence_penalty = data.get('presencePenalty', 0.0)

    # Check if message is safe
    is_safe, reason = is_prompt_safe(user_message)
    if not is_safe:
        return jsonify({'error': reason}), 403

    # Generate AI response
    response_text, input_tokens, output_tokens, estimated_cost = generate_ai_response(
        user_message=user_message,
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
def get_documents():
    """
    Get all documents in the knowledge base.
    
    Returns:
        JSON: List of documents
    """
    documents = list_documents()
    return jsonify(documents)

@api_bp.route('/documents/url', methods=['POST'])
def add_document_from_url():
    """
    Add a document from a URL to the knowledge base.
    
    Returns:
        JSON: Added document
    """
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Check if URL is safe
    is_safe, reason = is_prompt_safe(url)
    if not is_safe:
        return jsonify({'error': reason}), 403
    
    # Load document from URL
    documents = load_document_from_url(url)
    
    return jsonify({
        'message': f'Added {len(documents)} document chunks from URL',
        'document_count': len(documents)
    }), 201

@api_bp.route('/documents/file', methods=['POST'])
def add_document_from_file():
    """
    Add a document from a file to the knowledge base.
    
    Returns:
        JSON: Added document
    """
    try:
        print("Received file upload request")
        
        if 'file' not in request.files:
            print("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Processing file: {file.filename}")
        
        # Check file type
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['pdf', 'txt']:
            print(f"Unsupported file type: {file_extension}")
            return jsonify({'error': 'Unsupported file type. Only PDF and TXT files are supported.'}), 400
        
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            print(f"Saving to temporary file: {temp_file.name}")
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Load document from file
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"File size: {len(file_content)} bytes")
            
            # For large files, we might want to limit processing
            max_file_size = 10 * 1024 * 1024  # 10MB
            if len(file_content) > max_file_size:
                print(f"File too large: {len(file_content)} bytes")
                return jsonify({'error': f'File too large. Maximum size is {max_file_size/1024/1024}MB'}), 400
            
            print("Processing document content")
            documents = load_document_from_file(file.filename, file_content, file_extension)
            
            # Get the knowledge base directory path for the response
            kb_dir = os.path.abspath(KNOWLEDGE_BASE_DIR)
            
            print(f"Document processed successfully: {len(documents)} chunks")
            return jsonify({
                'message': f'Added {len(documents)} document chunks from file',
                'document_count': len(documents),
                'storage_info': f'Documents are stored in the knowledge base directory: {kb_dir}'
            }), 201
        except Exception as e:
            print(f"Error processing document: {str(e)}")
            return jsonify({'error': f'Error processing document: {str(e)}'}), 500
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"Temporary file removed: {temp_file_path}")
    except Exception as e:
        print(f"Unexpected error in file upload: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500 