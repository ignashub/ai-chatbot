import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Path to knowledge base files
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'knowledge_base')

# Ensure the knowledge base directory exists
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

# In-memory vector store
class SimpleVectorStore:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.initialized = False
    
    def add_document(self, document: Dict[str, Any], embedding: List[float]):
        """Add a document and its embedding to the store."""
        self.documents.append(document)
        self.embeddings.append(embedding)
        self.initialized = True
    
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for the most similar documents to the query."""
        if not self.initialized or not self.embeddings:
            return []
        
        # Convert embeddings to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        query_array = np.array(query_embedding)
        
        # Compute cosine similarity
        dot_product = np.dot(embeddings_array, query_array)
        norm_documents = np.linalg.norm(embeddings_array, axis=1)
        norm_query = np.linalg.norm(query_array)
        
        cosine_similarities = dot_product / (norm_documents * norm_query)
        
        # Get indices of top_k most similar documents
        top_indices = np.argsort(cosine_similarities)[-top_k:][::-1]
        
        # Return the top_k documents with their similarity scores
        results = []
        for idx in top_indices:
            if cosine_similarities[idx] > 0.7:  # Only return if similarity is above threshold
                results.append({
                    "document": self.documents[idx],
                    "similarity": float(cosine_similarities[idx])
                })
        
        return results

# Initialize vector store
vector_store = SimpleVectorStore()

# Converting the question to a vector embedding
def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI's embedding model."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def initialize_knowledge_base():
    """Initialize the knowledge base from files."""
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return
    
    # Check if there are any documents in the knowledge base
    has_documents = False
    for item in os.listdir(KNOWLEDGE_BASE_DIR):
        if item != ".gitkeep" and os.path.isdir(os.path.join(KNOWLEDGE_BASE_DIR, item)):
            has_documents = True
            break
    
    # If there are documents, load them
    if has_documents:
        load_documents_from_files()
        return
    
    # Otherwise, initialize with sample knowledge
    sample_knowledge = [
        {
            "title": "Benefits of Regular Exercise",
            "content": "Regular physical activity can improve your muscle strength and boost your endurance. Exercise delivers oxygen and nutrients to your tissues and helps your cardiovascular system work more efficiently. And when your heart and lung health improve, you have more energy to tackle daily chores. Regular exercise can help you: Control your weight, Reduce your risk of heart diseases, Help your body manage blood sugar and insulin levels, Help you quit smoking, Improve your mental health and mood, Strengthen your bones and muscles, Reduce your risk of some cancers, Improve your sleep, Reduce feelings of anxiety and depression, and Sharpen your thinking, learning, and judgment skills.",
            "source": "Health and Wellness Guide"
        },
        {
            "title": "Healthy Eating Guidelines",
            "content": "A healthy diet includes: Eating lots of vegetables and fruit, Eating plenty of foods with protein, Choosing whole grain foods, Limiting highly processed foods, Making water your drink of choice. Healthy eating is more than the foods you eat. It is also about where, when, why and how you eat. Healthy eating means eating a variety of foods that give you the nutrients you need to maintain your health, feel good, and have energy. These nutrients include protein, carbohydrates, fat, water, vitamins, and minerals.",
            "source": "Nutrition Handbook"
        },
        {
            "title": "Importance of Sleep",
            "content": "Sleep plays a vital role in good health and well-being throughout your life. Getting enough quality sleep at the right times can help protect your mental health, physical health, quality of life, and safety. During sleep, your body is working to support healthy brain function and maintain your physical health. In children and teens, sleep also helps support growth and development. The damage from sleep deficiency can occur in an instant (such as a car crash), or it can harm you over time. For example, ongoing sleep deficiency can raise your risk for some chronic health problems. It also can affect how well you think, react, work, learn, and get along with others.",
            "source": "Sleep Science Journal"
        },
        {
            "title": "Stress Management Techniques",
            "content": "Effective stress management techniques include: Regular physical activity, Relaxation techniques such as deep breathing, meditation, yoga, tai chi and massage, Keeping a sense of humor, Spending time with family and friends, Setting aside time for hobbies, such as reading a book or listening to music. Active coping is a form of coping that allows you to take charge of a situation and reduce the stress it causes. To actively cope with stress: Acknowledge your feelings, Focus on the positives, Find a way to let go of things beyond your control, Take action when you can make a difference, Have a plan and a backup plan, Ask for help.",
            "source": "Mental Health Guide"
        },
        {
            "title": "Hydration Importance",
            "content": "Drinking enough water each day is crucial for many reasons: to regulate body temperature, keep joints lubricated, prevent infections, deliver nutrients to cells, and keep organs functioning properly. Being well-hydrated also improves sleep quality, cognition, and mood. Experts recommend drinking roughly 11 cups of water per day for the average woman and 16 cups for men. However, water needs depend on many factors, including your health, how active you are and where you live. The best way to stay hydrated is to drink water throughout the day and eat foods with high water content like fruits and vegetables.",
            "source": "Hydration Research"
        },
        {
            "title": "Mental Health Maintenance",
            "content": "Good mental health is characterized by a person's ability to fulfill key functions and activities, including the ability to learn, the ability to feel, express and manage a range of positive and negative emotions, the ability to form and maintain good relationships with others, and the ability to cope with and manage change and uncertainty. To maintain good mental health: Stay positive, Practice gratitude, Take care of your physical health, Connect with others, Develop a sense of meaning and purpose, Develop coping skills, Meditate, and Get help when you need it.",
            "source": "Psychology Today"
        }
    ]
    
    # Add sample knowledge to the vector store
    for item in sample_knowledge:
        # Create a document with title, content, and source
        document = {
            "title": item["title"],
            "content": item["content"],
            "source": item["source"]
        }
        
        # Get embedding for the document
        embedding = get_embedding(item["title"] + " " + item["content"])
        
        # Add document and embedding to the vector store
        vector_store.add_document(document, embedding)
    
    print(f"Initialized knowledge base with {len(sample_knowledge)} documents")

def load_documents_from_files():
    """Load documents from files in the knowledge base directory."""
    loaded_count = 0
    
    for item in os.listdir(KNOWLEDGE_BASE_DIR):
        if item == ".gitkeep":
            continue
            
        doc_dir = os.path.join(KNOWLEDGE_BASE_DIR, item)
        if os.path.isdir(doc_dir):
            # Load document chunks
            for chunk_file in os.listdir(doc_dir):
                if chunk_file.endswith(".json") and chunk_file != "metadata.json":
                    chunk_path = os.path.join(doc_dir, chunk_file)
                    with open(chunk_path, "r") as f:
                        document = json.load(f)
                        
                        # Get embedding for the document
                        embedding = get_embedding(document["title"] + " " + document["content"])
                        
                        # Add document and embedding to the vector store
                        vector_store.add_document(document, embedding)
                        loaded_count += 1
    
    print(f"Loaded {loaded_count} document chunks from files")

def search_knowledge_base(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Search the knowledge base for relevant documents."""
    # Get embedding for the query
    query_embedding = get_embedding(query)
    
    # Search the vector store
    results = vector_store.search(query_embedding, top_k=top_k)
    
    return results

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
        document = result["document"]
        context += f"--- Document {i+1}: {document['title']} ---\n"
        context += f"{document['content']}\n\n"
    
    return context, True, [result["document"] for result in results]

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
initialize_knowledge_base() 