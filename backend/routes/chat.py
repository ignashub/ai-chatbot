from flask import Blueprint, jsonify, request
import os
import sys
from dotenv import load_dotenv
import re

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.ai_service import generate_ai_response_direct
from services.ai_service import generate_ai_response_with_function_calling
from services.function_definitions import function_definitions

# Load environment variables
load_dotenv()

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/message', methods=['POST'])
def send_message():
    """Process a chat message and return a response"""
    data = request.json
    message = data.get('message', '')
    system_prompt = data.get('systemPrompt', "You are a helpful assistant.")
    temperature = data.get('temperature', 0.7)
    top_p = data.get('topP', 1.0)
    frequency_penalty = data.get('frequencyPenalty', 0.0)
    presence_penalty = data.get('presencePenalty', 0.0)
    is_reminder_request = data.get('isReminderRequest', False)
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Check if this might be a reminder or nutrition request
        contains_reminder = is_reminder_request or re.search(r'remind|reminder|schedule|appointment', message.lower())
        contains_nutrition = re.search(r'nutrition|food|calorie|diet|eat', message.lower())
        
        # If it looks like a function calling request, use that path
        if contains_reminder or contains_nutrition:
            print(f"Detected potential function calling request: {message}")
            response_text, input_tokens, output_tokens, estimated_cost = generate_ai_response_with_function_calling(
                user_message=message,
                system_prompt=system_prompt,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                tools=function_definitions
            )
        else:
            # Use the direct function for regular queries
            response_text, input_tokens, output_tokens, estimated_cost = generate_ai_response_direct(
                user_message=message,
                system_prompt=system_prompt,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )
        
        return jsonify({
            "response": response_text,
            "estimated_cost": f"${estimated_cost:.6f}"
        })
    except Exception as e:
        import traceback
        print(f"Error in chat message endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500 