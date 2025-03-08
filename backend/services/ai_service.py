import os
import json
import sys
from openai import OpenAI
from langchain_openai import ChatOpenAI

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.token_counter import count_tokens
from utils.cost_calculator import calculate_cost
from services.function_calling import handle_function_call
from services.function_definitions import function_definitions

def generate_ai_response(user_message, system_prompt, model="gpt-4", temperature=0.7, 
                         top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0):
    """
    Generate a response from the AI model with function calling support.
    
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
    
    # Count input tokens
    input_text = f"{system_prompt}\n\nUser: {user_message}"
    input_tokens = count_tokens(input_text, model=model)
    
    # Prepare messages for the API call
    messages = [
        {"role": "system", "content": system_prompt},
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
        tool_choice="auto" #To let the AI decide when to call functions
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
    
    # Calculate cost
    estimated_cost = calculate_cost(input_tokens, output_tokens, model)
    
    return response_text, input_tokens, output_tokens, estimated_cost 