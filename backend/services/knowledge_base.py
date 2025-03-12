import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import openai
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Directory for storing knowledge base documents
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'knowledge_base')

# Ensure the knowledge base directory exists
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

class SimpleVectorStore:
    """A simple vector store for document embeddings."""
    
    def __init__(self):
        self.documents = []  # List of document dictionaries
        self.embeddings = []  # List of embedding vectors
    
    def add(self, document: Dict[str, Any], embedding: List[float]):
        """Add a document and its embedding to the store."""
        self.documents.append(document)
        self.embeddings.append(embedding)
    
    def add_document(self, document: Dict[str, Any], embedding: List[float]):
        """Alias for add method to maintain compatibility."""
        self.add(document, embedding)
    
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for documents similar to the query embedding."""
        if not self.embeddings:
            return []
        
        # Convert embeddings to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        query_array = np.array(query_embedding)
        
        # Calculate cosine similarity
        dot_product = np.dot(embeddings_array, query_array)
        norm_embeddings = np.linalg.norm(embeddings_array, axis=1)
        norm_query = np.linalg.norm(query_array)
        
        # Avoid division by zero
        similarities = dot_product / (norm_embeddings * norm_query + 1e-10)
        
        # Lower the threshold to 0.3 to catch more potential matches
        # Get indices of top_k most similar documents with similarity > 0.3
        indices = np.where(similarities > 0.3)[0]
        if len(indices) == 0:
            # If no results above threshold, just return top matches
            indices = np.argsort(-similarities)[:top_k]
        else:
            # Sort by similarity (descending)
            indices = indices[np.argsort(-similarities[indices])]
            indices = indices[:top_k]  # Take top_k
        
        # Return documents with similarity scores
        results = []
        for idx in indices:
            doc = self.documents[idx].copy()
            doc['similarity'] = float(similarities[idx])
            results.append(doc)
        
        return results

# Initialize vector store
vector_store = SimpleVectorStore()

# Load existing documents from the knowledge base directory
def load_existing_documents():
    """Load existing documents from the knowledge base directory."""
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        return
    
    # Iterate through document directories
    for doc_dir_name in os.listdir(KNOWLEDGE_BASE_DIR):
        doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, doc_dir_name)
        if not os.path.isdir(doc_dir):
            continue
        
        # Check for metadata file
        metadata_path = os.path.join(doc_dir, 'metadata.json')
        if not os.path.exists(metadata_path):
            continue
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Load document chunks
        for chunk_file in os.listdir(doc_dir):
            if not chunk_file.endswith('.json') or chunk_file == 'metadata.json':
                continue
            
            chunk_path = os.path.join(doc_dir, chunk_file)
            with open(chunk_path, 'r') as f:
                chunk_data = json.load(f)
                
                # Add to vector store
                if 'embedding' in chunk_data and 'content' in chunk_data:
                    document = {
                        'id': f"{doc_dir_name}_{chunk_file.split('.')[0]}",
                        'title': metadata.get('title', 'Untitled'),
                        'source': metadata.get('source', 'Unknown'),
                        'content': chunk_data['content'],
                        'date_added': metadata.get('date_added', datetime.now().isoformat())
                    }
                    vector_store.add(document, chunk_data['embedding'])

# Load existing documents on startup
load_existing_documents()

# Function to search the knowledge base
def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for documents similar to the query.
    
    Args:
        query: The query string
        top_k: The number of results to return
        
    Returns:
        List[Dict[str, Any]]: The search results
    """
    print(f"Searching knowledge base for: {query}")
    
    # Get the number of documents in the vector store
    print(f"Number of documents in vector store: {len(vector_store.documents)}")
    
    # Get embedding for the query
    query_embedding = get_embedding(query)
    
    # Search for similar documents
    results = vector_store.search(query_embedding, top_k=top_k)
    
    # Format results for return
    formatted_results = []
    for i, doc in enumerate(results):
        # Extract relevant information
        title = doc.get('title', 'Unknown')
        content = doc.get('content', '')
        source = doc.get('source', 'Unknown')
        similarity = doc.get('similarity', 0.0)
        
        print(f"Result {i+1}: {title} (similarity: {similarity:.4f})")
        
        # Add to formatted results
        formatted_results.append({
            'title': title,
            'content': content,
            'source': source,
            'similarity': similarity,
            'id': doc.get('id', f'unknown-{i}')
        })
    
    return formatted_results

# Simple embedding function (for demonstration)
def simple_embedding(text: str) -> List[float]:
    """
    Convert text to a simple embedding vector.
    
    This is an improved version that tries to capture more semantic meaning
    by using word-level hashing and TF-IDF like weighting.
    """
    import hashlib
    import math
    import re
    
    # Normalize text: lowercase and remove punctuation
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split into words and remove stop words
    words = text.split()
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'of'}
    words = [word for word in words if word not in stop_words]
    
    # Create a 128-dimensional vector
    embedding = [0.0] * 128
    
    # If no words, return zero vector
    if not words:
        return embedding
    
    # Count word occurrences for TF-IDF like weighting
    word_counts = {}
    for word in words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    
    # For each word, compute a hash and add to embedding
    for word, count in word_counts.items():
        # Hash the word
        hash_obj = hashlib.md5(word.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # Convert hash to indices and values
        for i in range(min(16, len(hash_bytes))):
            # Use each byte to determine an index in the embedding
            idx = hash_bytes[i] % 128
            
            # Weight by log(count+1) to simulate TF-IDF
            weight = math.log(count + 1)
            
            # Add to embedding at the determined index
            embedding[idx] += weight
    
    # Normalize the embedding
    norm = math.sqrt(sum(x*x for x in embedding))
    if norm > 0:
        embedding = [x/norm for x in embedding]
    
    return embedding

# Function to get embeddings for text - this is what document_loader.py is trying to import
def get_embedding(text: str) -> List[float]:
    """
    Get embedding for text using OpenAI's embedding model.
    
    In production, this would use a proper embedding model.
    For simplicity, we're using the simple_embedding function.
    
    Args:
        text: The text to get embedding for
        
    Returns:
        List[float]: The embedding vector
    """
    try:
        # For production, you would use OpenAI's embedding model
        # response = client.embeddings.create(
        #     input=text,
        #     model="text-embedding-ada-002"
        # )
        # return response.data[0].embedding
        
        # For simplicity, we'll use our simple embedding function
        return simple_embedding(text)
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        # Return a zero vector as fallback
        return [0.0] * 128

def get_rag_context(query: str) -> Tuple[str, bool, List[Dict[str, Any]]]:
    """
    Get RAG context for a query.
    
    Returns:
        Tuple[str, bool, List[Dict[str, Any]]]: The context, a boolean indicating if context was found, and the source documents
    """
    # Search the knowledge base
    results = search_knowledge_base(query)
    
    if not results:
        return "", False, []
    
    # Format the results as context
    context = "Here is some relevant information that might help answer the query:\n\n"
    
    for i, result in enumerate(results):
        context += f"--- Document {i+1}: {result['title']} ---\n"
        context += f"{result['content']}\n\n"
    
    return context, True, results

def format_citations(sources: List[Dict[str, Any]]) -> str:
    """
    Format citations for sources.
    
    Args:
        sources: List of source documents
        
    Returns:
        str: Formatted citations
    """
    if not sources:
        return ""
    
    citations = "\n\nSources:\n"
    
    # Track unique sources to avoid duplicates
    unique_sources = {}
    
    for i, source in enumerate(sources):
        # Use title and source as the key to avoid duplicates
        key = f"{source['title']}|{source.get('source', 'Unknown')}"
        
        if key not in unique_sources:
            unique_sources[key] = i + 1
            
            # Format the citation
            if 'source' in source and source['source'].startswith('http'):
                # It's a URL
                citations += f"[{i+1}] {source['title']} - {source['source']}\n"
            elif 'source' in source:
                # It's a document with a source
                citations += f"[{i+1}] {source['title']} - {source['source']}\n"
            else:
                # Just use the title
                citations += f"[{i+1}] {source['title']}\n"
    
    return citations

# Initialize the knowledge base when the module is imported
load_existing_documents() 