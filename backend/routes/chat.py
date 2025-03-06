from flask import Blueprint, request, jsonify
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.moderation import is_prompt_safe
from services.ai_service import generate_ai_response

# Create a Blueprint for chat routes
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['OPTIONS', 'POST'])
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
    system_prompt = data.get('systemPrompt', "You are a Health and Wellness Coach.")
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