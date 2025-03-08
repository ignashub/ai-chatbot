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

# Path to knowledge base files
from services.knowledge_base import KNOWLEDGE_BASE_DIR, get_embedding, vector_store

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
        print("Extracting text from PDF")
        pdf_file = BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        print(f"PDF has {len(pdf_reader.pages)} pages")
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text() or ""
                text += page_text + "\n"
                print(f"Extracted {len(page_text)} characters from page {page_num+1}")
            except Exception as e:
                print(f"Error extracting text from page {page_num+1}: {e}")
                # Continue with next page instead of failing completely
                text += f"[Error extracting page {page_num+1}]\n"
        
        if not text.strip():
            print("No text extracted from PDF")
            return "No text could be extracted from this PDF. It may be scanned or contain only images."
        
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return f"Error extracting content: {str(e)}"

def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into chunks of maximum size with overlap.
    
    Args:
        text: The text to chunk
        max_chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # If we're not at the end of the text, try to find a good breaking point
        if end < len(text):
            # Try to find a period, question mark, or exclamation point followed by a space
            match = re.search(r'[.!?]\s', text[end-100:end])
            if match:
                end = end - 100 + match.end()
            else:
                # If no good breaking point, try to find a space
                match = re.search(r'\s', text[end-50:end])
                if match:
                    end = end - 50 + match.end()
        
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks

def load_document_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Load a document from a URL and add it to the knowledge base.
    
    Args:
        url: The URL to load
        
    Returns:
        List[Dict[str, Any]]: The loaded document chunks with metadata
    """
    # Extract text from URL
    title, content = extract_text_from_url(url)
    
    # Generate a unique ID for the document
    doc_id = hashlib.md5(url.encode()).hexdigest()
    
    # Chunk the content
    chunks = chunk_text(content)
    
    # Create document objects
    documents = []
    for i, chunk in enumerate(chunks):
        document = {
            "id": f"{doc_id}-{i}",
            "title": title,
            "content": chunk,
            "source": url,
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
        documents.append(document)
        
        # Get embedding for the document
        embedding = get_embedding(title + " " + chunk)
        
        # Add document and embedding to the vector store
        vector_store.add_document(document, embedding)
    
    # Save document to file
    save_document_to_file(documents)
    
    return documents

def load_document_from_file(file_path: str, file_content: bytes, file_type: str) -> List[Dict[str, Any]]:
    """
    Load a document from a file and add it to the knowledge base.
    
    Args:
        file_path: The path to the file
        file_content: The file content as bytes
        file_type: The file type (e.g., 'pdf', 'txt')
        
    Returns:
        List[Dict[str, Any]]: The loaded document chunks with metadata
    """
    # Extract text from file
    if file_type == 'pdf':
        content = extract_text_from_pdf(file_content)
        title = os.path.basename(file_path)
    elif file_type == 'txt':
        content = file_content.decode('utf-8')
        title = os.path.basename(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # Generate a unique ID for the document
    # Use the filename and content hash instead of file modification time
    content_hash = hashlib.md5(file_content).hexdigest()
    doc_id = hashlib.md5((file_path + content_hash).encode()).hexdigest()
    
    # Chunk the content
    chunks = chunk_text(content)
    
    # Create document objects
    documents = []
    for i, chunk in enumerate(chunks):
        document = {
            "id": f"{doc_id}-{i}",
            "title": title,
            "content": chunk,
            "source": file_path,
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
        documents.append(document)
        
        # Get embedding for the document
        embedding = get_embedding(title + " " + chunk)
        
        # Add document and embedding to the vector store
        vector_store.add_document(document, embedding)
    
    # Save document to file
    save_document_to_file(documents)
    
    return documents

def save_document_to_file(documents: List[Dict[str, Any]]) -> None:
    """
    Save document chunks to files in the knowledge base directory.
    
    Args:
        documents: List of document chunks with metadata
    """
    if not documents:
        return
    
    # Create a directory for the document
    doc_id = documents[0]["id"].split("-")[0]
    doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, doc_id)
    os.makedirs(doc_dir, exist_ok=True)
    
    # Save document metadata
    metadata = {
        "id": doc_id,
        "title": documents[0]["title"],
        "source": documents[0]["source"],
        "total_chunks": documents[0]["total_chunks"],
        "chunks": [doc["id"] for doc in documents]
    }
    
    with open(os.path.join(doc_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Save each chunk
    for doc in documents:
        chunk_file = os.path.join(doc_dir, f"{doc['id']}.json")
        with open(chunk_file, "w") as f:
            json.dump(doc, f, indent=2)

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