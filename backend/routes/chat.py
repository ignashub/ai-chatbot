from flask import Blueprint, request, jsonify
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.moderation import is_prompt_safe
from services.ai_service import generate_ai_response
from services.function_calling import get_all_reminders, search_nutrition

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
    system_prompt = data.get('systemPrompt', "You are a Health and Wellness Coach. You can help set reminders for health activities and provide nutrition information for food items.")
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

@chat_bp.route('/reminders', methods=['GET'])
def reminders():
    """
    Get all reminders.
    
    Returns:
        JSON: List of all reminders
    """
    return jsonify(get_all_reminders())

@chat_bp.route('/nutrition', methods=['GET', 'POST'])
def nutrition():
    """
    Search for nutrition information about a food item.
    
    Returns:
        JSON: Nutrition information
    """
    if request.method == 'GET':
        # Handle GET request with query parameters
        food_item = request.args.get('food_item')
        quantity = request.args.get('quantity', 100)
        unit = request.args.get('unit', 'g')
        
        if not food_item:
            return jsonify({'error': 'Food item is required'}), 400
        
        try:
            quantity = float(quantity)
        except ValueError:
            return jsonify({'error': 'Quantity must be a number'}), 400
        
        result = search_nutrition(food_item, quantity, unit)
        return jsonify(result)
    
    elif request.method == 'POST':
        # Handle POST request with JSON body
        data = request.json
        food_item = data.get('food_item')
        quantity = data.get('quantity', 100)
        unit = data.get('unit', 'g')
        
        if not food_item:
            return jsonify({'error': 'Food item is required'}), 400
        
        result = search_nutrition(food_item, quantity, unit)
        return jsonify(result)