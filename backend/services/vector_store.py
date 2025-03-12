import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
import re

# Import constants
from .knowledge_base import KNOWLEDGE_BASE_DIR

class VectorStore:
    def __init__(self):
        self.documents = []
        self.embeddings = []
    
    def add_document(self, document: Dict[str, Any], embedding: List[float]) -> None:
        """
        Add a document and its embedding to the vector store.
        
        Args:
            document: The document to add
            embedding: The document embedding
        """
        self.documents.append(document)
        self.embeddings.append(embedding)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query embedding.
        
        Args:
            query_embedding: The query embedding
            top_k: The number of results to return
            
        Returns:
            List[Dict[str, Any]]: The search results
        """
        if not self.embeddings or not self.documents:
            print("Warning: No documents or embeddings in vector store")
            return []
        
        try:
            # Convert embeddings to numpy array for faster computation
            embeddings_array = np.array(self.embeddings)
            query_array = np.array(query_embedding)
            
            # Compute cosine similarity
            dot_product = np.dot(embeddings_array, query_array)
            norm_embeddings = np.linalg.norm(embeddings_array, axis=1)
            norm_query = np.linalg.norm(query_array)
            
            # Avoid division by zero
            similarities = dot_product / (norm_embeddings * norm_query + 1e-10)
            
            # Get top k indices
            top_indices = np.argsort(similarities)[::-1][:top_k * 2]  # Get more candidates initially
            
            # Return top k documents with their similarity scores
            results = []
            for idx in top_indices:
                if idx < len(self.documents):  # Ensure index is valid
                    doc = self.documents[idx].copy()  # Make a copy to avoid modifying original
                    similarity = float(similarities[idx])
                    
                    # Add similarity score to document
                    doc['similarity'] = similarity
                    
                    # Print debug info
                    print(f"Search result: {doc.get('title', 'Unknown')} (id: {doc.get('id', 'Unknown')}, similarity: {similarity:.4f})")
                    
                    # Ensure document has all required fields
                    if 'title' not in doc:
                        doc['title'] = 'Unknown'
                    if 'content' not in doc:
                        doc['content'] = 'No content available'
                    if 'source' not in doc:
                        doc['source'] = 'Unknown'
                    
                    # Clean up content if needed - add spaces between words that are run together
                    if 'content' in doc and isinstance(doc['content'], str):
                        # Fix common OCR issues where words are run together
                        doc['content'] = re.sub(r'([a-z])([A-Z])', r'\1 \2', doc['content'])
                    
                    results.append(doc)
            
            # If searching for a specific document (indicated by a high top_k value),
            # try to ensure we have a good representation of the document
            if top_k > 5:
                # Group results by document title
                docs_by_title = {}
                for doc in results:
                    title = doc.get('title', 'Unknown')
                    if title not in docs_by_title:
                        docs_by_title[title] = []
                    docs_by_title[title].append(doc)
                
                # If we have multiple documents, prioritize the ones with more chunks
                # This helps ensure we get more complete information from the most relevant document
                if len(docs_by_title) > 1:
                    # Sort titles by number of chunks (descending)
                    sorted_titles = sorted(docs_by_title.keys(), 
                                          key=lambda t: len(docs_by_title[t]), 
                                          reverse=True)
                    
                    # Reorder results to prioritize documents with more chunks
                    reordered_results = []
                    for title in sorted_titles:
                        # Sort chunks by their position in the document if possible
                        chunks = docs_by_title[title]
                        try:
                            chunks = sorted(chunks, key=lambda x: int(x.get('id', '0').split('-')[-1]) if x.get('id', '0').split('-')[-1].isdigit() else 0)
                        except:
                            pass  # If sorting fails, use the original order
                        
                        reordered_results.extend(chunks)
                    
                    # Trim to original top_k size if needed
                    results = reordered_results[:top_k]
                else:
                    # If only one document, try to get consecutive chunks
                    for title in docs_by_title:
                        chunks = docs_by_title[title]
                        if len(chunks) > 1:
                            # Try to sort chunks by ID to get consecutive sections
                            try:
                                chunks = sorted(chunks, key=lambda x: int(x.get('id', '0').split('-')[-1]) if x.get('id', '0').split('-')[-1].isdigit() else 0)
                                docs_by_title[title] = chunks
                            except:
                                pass  # If sorting fails, use the original order
                    
                    # Flatten the dictionary back to a list
                    results = []
                    for title in docs_by_title:
                        results.extend(docs_by_title[title])
                    
                    # Trim to original top_k size if needed
                    results = results[:top_k]
            
            return results
        except Exception as e:
            import traceback
            print(f"Error in vector store search: {e}")
            print(traceback.format_exc())
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            Optional[Dict[str, Any]]: The document or None if not found
        """
        try:
            # Check if the document exists in memory
            for doc in self.documents:
                if doc.get('id') == document_id:
                    return doc
            
            # If not found in memory, try to load from disk
            doc_parts = document_id.split('-')
            if len(doc_parts) > 1:
                base_id = doc_parts[0]
                chunk_index = doc_parts[1]
                
                # Try to load from the document directory
                doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, base_id)
                if os.path.exists(doc_dir):
                    chunk_file = os.path.join(doc_dir, f"{chunk_index}.json")
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'r') as f:
                            return json.load(f)
            
            return None
        except Exception as e:
            print(f"Error getting document {document_id}: {e}")
            return None

# Create a global instance of the vector store
vector_store = VectorStore() 