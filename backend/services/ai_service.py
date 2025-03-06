import os
import sys
from langchain_openai import ChatOpenAI

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.token_counter import count_tokens
from utils.cost_calculator import calculate_cost

def generate_ai_response(user_message, system_prompt, model="gpt-4", temperature=0.7, 
                         top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
    """
    Generate a response from the AI model.
    
    Args:
        user_message (str): The user's message
        system_prompt (str): The system prompt to set context
        model (str): The model to use (default: "gpt-4")
        temperature (float): Controls randomness (default: 0.7)
        top_p (float): Controls diversity (default: 1.0)
        frequency_penalty (float): Penalizes repeated tokens (default: 0.0)
        presence_penalty (float): Encourages new topics (default: 0.0)
        
    Returns:
        tuple: (response_text, input_tokens, output_tokens, estimated_cost)
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Initialize OpenAI
    llm = ChatOpenAI(
        api_key=api_key, 
        model_name=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    
    # Count input tokens
    input_text = f"{system_prompt}\n\nUser: {user_message}"
    input_tokens = count_tokens(input_text, model=model)
    
    # Generate response
    response = llm.invoke(
        f"{system_prompt}\n\nUser: {user_message}\nBot:"
    )
    
    # Count output tokens
    output_tokens = count_tokens(response.content, model=model)
    
    # Calculate cost
    estimated_cost = calculate_cost(input_tokens, output_tokens, model)
    
    return response.content, input_tokens, output_tokens, estimated_cost 