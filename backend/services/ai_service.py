import os
import json
import sys
from openai import OpenAI
from langchain_openai import ChatOpenAI
from typing import Tuple, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.token_counter import count_tokens
from utils.cost_calculator import calculate_cost
from services.function_calling import handle_function_call
from services.function_definitions import function_definitions
from services.knowledge_base import get_rag_context, format_citations

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_ai_response(user_message, system_prompt=None, model="gpt-4", temperature=0.7, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
    """
    Generate a response from the AI model.
    
    Args:
        user_message (str): The user's message
        system_prompt (str): The system prompt to use
        model (str): The model to use
        temperature (float): The temperature parameter
        top_p (float): The top_p parameter
        frequency_penalty (float): The frequency penalty parameter
        presence_penalty (float): The presence penalty parameter
        
    Returns:
        tuple: (response_text, input_tokens, output_tokens, estimated_cost)
    """
    print(f"AI Service received system prompt: {system_prompt}")  # Debug log
    
    # Default system prompt if none provided
    if system_prompt is None or system_prompt.strip() == "":
        system_prompt = "You are a Health and Wellness Coach with access to a knowledge base of health documents. When answering questions about documents, thoroughly search for relevant information and present it accurately. Include specific details from the documents when available, such as measurement methods, frameworks, or tools. Balance comprehensive answers with clarity. You can also help set reminders for health activities and provide nutrition information for food items."
    
    try:
        print(f"Generating AI response for message: {user_message[:100]}...")
        
        # Check if this is a document query (contains document context)
        is_document_query = "Here is information from the documents you asked about:" in user_message or "IMPORTANT SECTION" in user_message
        
        # For document queries, use a lower temperature to get more factual responses
        if is_document_query:
            temperature = min(temperature, 0.5)
            print(f"Document query detected, using lower temperature: {temperature}")
        
        # Create the messages array
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Get token usage
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        # Calculate estimated cost
        # These are approximate costs and may change
        if model == "gpt-4":
            input_cost_per_1k = 0.03
            output_cost_per_1k = 0.06
        else:  # Default to gpt-3.5-turbo pricing
            input_cost_per_1k = 0.0015
            output_cost_per_1k = 0.002
        
        estimated_cost = (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)
        
        return response_text, input_tokens, output_tokens, estimated_cost
    except Exception as e:
        print(f"Error generating AI response: {str(e)}")
        # Return a default response in case of error
        return f"I'm sorry, I encountered an error: {str(e)}", 0, 0, 0.0

def generate_ai_response_with_function_calling(user_message, system_prompt, model="gpt-4", temperature=0.7, 
                         top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
    """
    Generate a response from the AI model with function calling support and RAG.
    
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
    client = OpenAI(api_key=api_key)
    
    # Print the system prompt for debugging
    print(f"RAG function received system prompt: {system_prompt}")
    
    # Get RAG context if available
    rag_context, has_context, source_documents = get_rag_context(user_message)
    
    # Prepare system prompt with RAG context if available
    # IMPORTANT: Use the provided system prompt as the base, don't override it
    enhanced_system_prompt = system_prompt
    
    # Only add RAG-specific instructions if they're not already in the system prompt
    if has_context and "knowledge base" not in system_prompt.lower():
        enhanced_system_prompt += "\n\nI have access to information from documents that have been uploaded to my knowledge base. "
        enhanced_system_prompt += rag_context
        enhanced_system_prompt += "\n\nWhen using information from these documents, please cite the sources in your response using numbers in square brackets, e.g., [1], [2], etc. If asked about uploaded documents, please use this information to provide a response."
    elif "knowledge base" not in system_prompt.lower():
        # Even if no specific context is found, let the model know about the capability
        enhanced_system_prompt += "\n\nI can access information from documents that have been uploaded to my knowledge base, but I don't see any relevant information for this query. If you're asking about a document you've uploaded, please provide more specific details about what you're looking for."
    
    # Print the enhanced system prompt for debugging
    print(f"Enhanced system prompt: {enhanced_system_prompt[:100]}...")
    
    # Count input tokens
    input_text = f"{enhanced_system_prompt}\n\nUser: {user_message}"
    input_tokens = count_tokens(input_text, model=model)
    
    # Prepare messages for the API call
    messages = [
        {"role": "system", "content": enhanced_system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # Make the API call with function calling
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        tools=function_definitions,
        tool_choice="auto"
    )
    
    # Process the response
    response_message = response.choices[0].message
    
    # Check if the model wants to call a function
    if response_message.tool_calls:
        # Process each function call
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the function
            function_response = handle_function_call(function_name, function_args)
            
            # Add the function call and response to the conversation
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                ]
            })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(function_response)
            })
        
        # Get a new response from the model with the function results
        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        
        response_text = second_response.choices[0].message.content
        
        # Count output tokens (including both responses)
        output_tokens = response.usage.completion_tokens + second_response.usage.completion_tokens
        
        # Update input tokens to include the function call and response
        input_tokens = response.usage.prompt_tokens + second_response.usage.prompt_tokens - output_tokens
    else:
        # No function call, just return the response
        response_text = response_message.content
        output_tokens = response.usage.completion_tokens
    
    # Add citations if we used RAG
    if has_context and source_documents:
        citations = format_citations(source_documents)
        response_text += citations
    
    # Calculate cost
    estimated_cost = calculate_cost(input_tokens, output_tokens, model)
    
    return response_text, input_tokens, output_tokens, estimated_cost 

def generate_ai_response_direct(user_message, system_prompt, model="gpt-4", temperature=0.7, 
                         top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
    """
    Generate a response from the AI model directly using the provided system prompt without any modifications.
    This is a simplified version that doesn't use RAG or function calling.
    
    Args:
        user_message (str): The user's message
        system_prompt (str): The system prompt to set context (used exactly as provided)
        model (str): The model to use (default: "gpt-4")
        temperature (float): Controls randomness (default: 0.7)
        top_p (float): Controls diversity (default: 1.0)
        frequency_penalty (float): Penalizes repeated tokens (default: 0.0)
        presence_penalty (float): Encourages new topics (default: 0.0)
        
    Returns:
        tuple: (response_text, input_tokens, output_tokens, estimated_cost)
    """
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)
    
    print(f"Direct function using system prompt exactly as provided: {system_prompt}")
    
    # Prepare messages for the API call - use system prompt exactly as provided
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    print(f"Sending messages to OpenAI API: {json.dumps(messages, indent=2)}")
    
    # Call the OpenAI API
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    
    # Extract the response text
    response_text = response.choices[0].message.content
    
    print(f"Received response from OpenAI API: {response_text[:100]}...")
    
    # Get token usage
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    
    # Calculate estimated cost
    if model == "gpt-4":
        input_cost_per_1k = 0.03
        output_cost_per_1k = 0.06
    else:  # Default to gpt-3.5-turbo pricing
        input_cost_per_1k = 0.0015
        output_cost_per_1k = 0.002
    
    estimated_cost = (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)
    
    return response_text, input_tokens, output_tokens, estimated_cost 