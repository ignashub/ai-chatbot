import os
import re
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import hashlib
from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO
import tempfile
from datetime import datetime
import uuid

# Path to knowledge base files
from services.knowledge_base import KNOWLEDGE_BASE_DIR, get_embedding, vector_store

# Import the logging function from routes.api
# This is a circular import, but we'll handle it by importing inside functions
def log_message(message):
    """Log a message to both console and the processing logs."""
    print(message)
    try:
        from routes.api import add_processing_log
        add_processing_log(message)
    except ImportError:
        # If we can't import, just print to console
        pass

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for filesystem."""
    # Remove invalid characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    return filename

def extract_text_from_url(url: str) -> Tuple[str, str]:
    """
    Extract text content from a URL.
    
    Args:
        url: The URL to extract text from
        
    Returns:
        Tuple[str, str]: The title and content of the webpage
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else url
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text (remove extra whitespace)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return title, text
    except Exception as e:
        print(f"Error extracting text from URL {url}: {e}")
        return url, f"Error extracting content: {str(e)}"

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_content: The PDF file content as bytes
        
    Returns:
        str: The extracted text
    """
    try:
        log_message("Extracting text from PDF")
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        log_message(f"PDF has {len(pdf_reader.pages)} pages")
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text() or ""
                text += page_text + "\n"
                log_message(f"Extracted {len(page_text)} characters from page {page_num+1}")
            except Exception as e:
                log_message(f"Error extracting text from page {page_num+1}: {e}")
                # Continue with next page instead of failing completely
                text += f"[Error extracting page {page_num+1}]\n"
        
        if not text.strip():
            log_message("No text extracted from PDF")
            return "No text could be extracted from this PDF. It may be scanned or contain only images."
        
        return text
    except Exception as e:
        log_message(f"Error extracting text from PDF: {e}")
        return f"Error extracting content: {str(e)}"

def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks of maximum size with overlap.
    
    Args:
        text: The text to chunk
        max_chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List[str]: List of text chunks
    """
    log_message(f"Starting text chunking process for {len(text)} characters")
    
    if len(text) <= max_chunk_size:
        log_message(f"Text is smaller than max chunk size, returning as single chunk")
        return [text]
    
    # Clean the text - remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    log_message(f"Cleaned text, now {len(text)} characters")
    
    chunks = []
    start = 0
    
    # Safety counter to prevent infinite loops
    iteration_count = 0
    max_iterations = len(text) * 2  # This should be more than enough
    
    while start < len(text) and iteration_count < max_iterations:
        iteration_count += 1
        
        # Calculate end position
        end = min(start + max_chunk_size, len(text))
        
        # If we're not at the end of the text, try to find a good breaking point
        if end < len(text):
            # Look back from end to find a good breaking point
            search_start = max(0, end - 200)
            search_end = min(len(text), end + 200)
            search_text = text[search_start:search_end]
            
            # Try to find paragraph breaks first
            paragraph_match = re.search(r'\n\s*\n', search_text)
            if paragraph_match:
                end = search_start + paragraph_match.start() + 1
            else:
                # Try to find a sentence end
                sentence_match = re.search(r'[.!?]\s', search_text)
                if sentence_match:
                    end = search_start + sentence_match.end()
                else:
                    # If no good breaking point, try to find a space
                    space_match = re.search(r'\s', search_text)
                    if space_match:
                        end = search_start + space_match.end()
        
        # Ensure we're making progress
        if end <= start:
            log_message(f"Warning: Chunking not making progress at position {start}, forcing advance")
            end = min(start + max_chunk_size, len(text))
        
        # Get the chunk
        chunk = text[start:end].strip()
        
        # Only add non-empty chunks
        if chunk:
            chunks.append(chunk)
            
            # Log progress periodically
            if len(chunks) % 5 == 0:
                log_message(f"Created {len(chunks)} chunks so far")
        
        # Move to next chunk with overlap
        start = end - overlap
        
        # Ensure we're making progress
        if start < end - max_chunk_size:
            log_message(f"Warning: Overlap too large, adjusting to ensure progress")
            start = end - min(overlap, max_chunk_size // 2)
    
    if iteration_count >= max_iterations:
        log_message(f"Warning: Reached maximum iterations ({max_iterations}), stopping chunking process")
    
    log_message(f"Chunking complete. Created {len(chunks)} chunks from {len(text)} characters")
    return chunks

def add_document_from_text(text: str, title: str, source: str, doc_id: str = None) -> List[Dict[str, Any]]:
    """
    Add a document to the knowledge base from text.
    
    Args:
        text: The document text
        title: The document title
        source: The document source
        doc_id: Optional document ID (will be generated if not provided)
        
    Returns:
        List[Dict[str, Any]]: The added document chunks
    """
    log_message(f"Adding document from text: {title}")
    
    if not doc_id:
        doc_id = str(uuid.uuid4())
        log_message(f"Generated document ID: {doc_id}")
    
    # Create a directory for the document
    doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, doc_id)
    os.makedirs(doc_dir, exist_ok=True)
    log_message(f"Created document directory: {doc_dir}")
    
    # Chunk the text - use the global function, not a local variable
    log_message(f"Chunking text of length {len(text)} characters")
    text_chunks = chunk_text(text)
    log_message(f"Text chunking complete. Created {len(text_chunks)} chunks")
    
    # Create document objects
    documents = []
    log_message(f"Processing {len(text_chunks)} chunks")
    
    # Save metadata first with in_progress status
    metadata = {
        "id": doc_id,
        "title": title,
        "source": source,
        "total_chunks": len(text_chunks),
        "processing_status": "in_progress",
        "date_added": datetime.now().isoformat()
    }
    
    with open(os.path.join(doc_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Process chunks in batches
    batch_size = 5
    total_batches = (len(text_chunks) + batch_size - 1) // batch_size
    
    for i in range(0, len(text_chunks), batch_size):
        batch = text_chunks[i:i+batch_size]
        current_batch = i//batch_size + 1
        log_message(f"Processing batch {current_batch}/{total_batches}")
        
        for j, chunk in enumerate(batch):
            chunk_index = i + j
            document = {
                "id": f"{doc_id}-{chunk_index}",
                "title": title,
                "content": chunk,
                "source": source,
                "chunk_index": chunk_index,
                "total_chunks": len(text_chunks)
            }
            documents.append(document)
            
            # Get embedding for the document
            embedding = get_embedding(title + " " + chunk)
            
            # Add document and embedding to the vector store
            vector_store.add_document(document, embedding)
            
            # Save chunk to file
            chunk_file = os.path.join(doc_dir, f"{chunk_index}.json")
            doc_with_embedding = document.copy()
            doc_with_embedding["embedding"] = embedding
            with open(chunk_file, "w") as f:
                json.dump(doc_with_embedding, f, indent=2)
        
        # Update progress
        log_message(f"Processed and saved batch {current_batch}/{total_batches}")
    
    # Update metadata with final information
    metadata["chunks"] = [doc["id"] for doc in documents]
    metadata["processing_status"] = "complete"
    
    with open(os.path.join(doc_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    log_message(f"Successfully processed document with {len(documents)} chunks")
    log_message(f"Document processing complete for {title}")
    return documents

def load_document_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Load a document from a URL.
    
    Args:
        url: The URL to load the document from
        
    Returns:
        List of document chunks
    """
    try:
        log_message(f"Attempting to load document from URL: {url}")
        
        # Send a request to the URL with a timeout and proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        log_message(f"Sending request to {url}")
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        
        # Get content type and filename
        content_type = response.headers.get('Content-Type', '').lower()
        log_message(f"Content type: {content_type}")
        
        # Try to get filename from Content-Disposition header or URL
        filename = None
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition and 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
        
        if not filename:
            # Extract filename from URL
            parsed_url = urlparse(url)
            path = parsed_url.path
            filename = os.path.basename(path)
        
        log_message(f"Filename: {filename}")
        
        # Determine file type
        file_extension = filename.split('.')[-1].lower() if '.' in filename else None
        
        # If content type is HTML or no file extension, treat as HTML
        if 'text/html' in content_type or not file_extension:
            log_message("Detected HTML content")
            html_content = response.text
            # Create a document ID
            doc_id = str(uuid.uuid4())
            # Add the HTML content to the knowledge base
            documents = add_document_from_text(
                text=html_content,
                title=filename or "Web Page",
                source=url,
                doc_id=doc_id
            )
            return documents
        
        # Handle PDF files
        elif 'application/pdf' in content_type or file_extension == 'pdf':
            log_message("Detected file type: pdf")
            # Save PDF to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                log_message(f"Downloading PDF to {temp_file.name}")
                # Stream the content to avoid loading large files into memory
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Process the PDF
                log_message(f"Processing PDF from {temp_file_path}")
                return process_pdf(temp_file_path, filename, url)
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    log_message(f"Removed temporary file: {temp_file_path}")
        
        # Handle text files
        elif 'text/plain' in content_type or file_extension in ['txt', 'text']:
            log_message("Detected file type: text")
            text_content = response.text
            # Create a document ID
            doc_id = str(uuid.uuid4())
            # Add the text content to the knowledge base
            documents = add_document_from_text(
                text=text_content,
                title=filename or "Text Document",
                source=url,
                doc_id=doc_id
            )
            return documents
        
        else:
            log_message(f"Unsupported content type: {content_type}")
            return []
    
    except requests.exceptions.RequestException as e:
        log_message(f"Request error: {str(e)}")
        return []
    except Exception as e:
        log_message(f"Error loading document from URL: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
        return []

def process_pdf(pdf_path, filename, source):
    """
    Process a PDF file and add its content to the knowledge base.
    
    Args:
        pdf_path: Path to the PDF file
        filename: Original filename
        source: Source of the document
        
    Returns:
        list: List of document chunks added to the knowledge base
    """
    try:
        log_message("Extracting text from PDF")
        
        # Create a document ID
        doc_id = str(uuid.uuid4())
        
        # Create a directory for the document
        doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        # Extract text from PDF
        all_text = ""
        
        # Use PyPDF2 to extract text
        with open(pdf_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                log_message(f"PDF has {total_pages} pages")
                
                # Process each page with error handling
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text() or ""
                        log_message(f"Extracted {len(page_text)} characters from page {i+1}")
                        all_text += page_text + "\n\n"
                        
                        # Periodically save progress for very large PDFs
                        if (i+1) % 20 == 0 and i > 0:
                            log_message(f"Progress: {i+1}/{total_pages} pages processed")
                    except Exception as e:
                        log_message(f"Error extracting text from page {i+1}: {str(e)}")
                        continue
            except Exception as e:
                log_message(f"Error reading PDF: {str(e)}")
                raise
        
        # If no text was extracted, return empty list
        if not all_text.strip():
            log_message("No text could be extracted from the PDF")
            return []
        
        log_message(f"Text extraction complete. Total characters: {len(all_text)}")
        
        # Save metadata first
        metadata = {
            "id": doc_id,
            "title": filename,
            "source": source,
            "date_added": datetime.now().isoformat(),
            "file_type": "pdf",
            "processing_status": "in_progress"
        }
        
        with open(os.path.join(doc_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        log_message(f"Saved metadata for document {doc_id}")
        
        # Process in smaller batches to avoid memory issues
        log_message(f"Chunking text (total length: {len(all_text)} characters)")
        text_chunks = chunk_text(all_text)
        log_message(f"Created {len(text_chunks)} chunks")
        
        # Create document objects and add to vector store in batches
        documents = []
        batch_size = 5  # Process 5 chunks at a time
        total_batches = (len(text_chunks) + batch_size - 1) // batch_size
        
        log_message(f"Starting to process {len(text_chunks)} chunks in {total_batches} batches")
        
        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i:i+batch_size]
            current_batch = i//batch_size + 1
            log_message(f"Processing batch {current_batch}/{total_batches}")
            
            batch_docs = []
            for j, chunk in enumerate(batch):
                chunk_index = i + j
                document = {
                    "id": f"{doc_id}-{chunk_index}",
                    "title": filename,
                    "content": chunk,
                    "source": source,
                    "chunk_index": chunk_index,
                    "total_chunks": len(text_chunks)
                }
                batch_docs.append(document)
                documents.append(document)
                
                # Get embedding for the document
                embedding = get_embedding(filename + " " + chunk)
                
                # Add document and embedding to the vector store
                vector_store.add_document(document, embedding)
                
                # Save chunk to file
                chunk_file = os.path.join(doc_dir, f"{chunk_index}.json")
                doc_with_embedding = document.copy()
                doc_with_embedding["embedding"] = embedding
                with open(chunk_file, "w") as f:
                    json.dump(doc_with_embedding, f, indent=2)
            
            # Update progress after each batch
            log_message(f"Processed and saved batch {current_batch}/{total_batches}")
            
            # Update metadata with progress
            metadata["processing_progress"] = f"{current_batch}/{total_batches} batches"
            with open(os.path.join(doc_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
        
        # Update metadata with final chunk count
        metadata["total_chunks"] = len(text_chunks)
        metadata["chunks"] = [doc["id"] for doc in documents]
        metadata["processing_status"] = "complete"
        
        with open(os.path.join(doc_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        log_message(f"Successfully processed document with {len(documents)} chunks")
        log_message(f"Document processing complete for {filename}")
        return documents
    
    except Exception as e:
        log_message(f"Error processing PDF: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
        log_message("Document processing failed")
        return []

def load_document_from_file(filename, file_content, file_extension):
    """
    Load a document from a file.
    
    Args:
        filename: The name of the file
        file_content: The content of the file
        file_extension: The extension of the file
        
    Returns:
        list: List of document chunks added to the knowledge base
    """
    try:
        # Create a document ID
        doc_id = str(uuid.uuid4())
        
        # Handle different file types
        if file_extension.lower() == 'pdf':
            # Save PDF to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Process the PDF
                return process_pdf(temp_file_path, filename, f"Uploaded file: {filename}")
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        
        elif file_extension.lower() == 'txt':
            # Process text file
            text_content = file_content.decode('utf-8', errors='replace')
            
            # Add the text to the knowledge base
            documents = add_document_from_text(
                text=text_content,
                title=filename,
                source=f"Uploaded file: {filename}",
                doc_id=doc_id
            )
            
            return documents
        
        else:
            log_message(f"Unsupported file extension: {file_extension}")
            return []
    
    except Exception as e:
        log_message(f"Error loading document from file: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
        return []

def get_document_metadata(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a document.
    
    Args:
        doc_id: The document ID
        
    Returns:
        Optional[Dict[str, Any]]: The document metadata, or None if not found
    """
    doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, doc_id)
    metadata_file = os.path.join(doc_dir, "metadata.json")
    
    if not os.path.exists(metadata_file):
        return None
    
    with open(metadata_file, "r") as f:
        return json.load(f)

def list_documents() -> List[Dict[str, Any]]:
    """
    List all documents in the knowledge base.
    
    Returns:
        List[Dict[str, Any]]: List of document metadata
    """
    documents = []
    
    for item in os.listdir(KNOWLEDGE_BASE_DIR):
        if item == ".gitkeep":
            continue
            
        doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, item)
        if os.path.isdir(doc_dir):
            metadata_file = os.path.join(doc_dir, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    documents.append(metadata)
    
    return documents 