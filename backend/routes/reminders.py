from flask import Blueprint, jsonify, request
from services.function_calling import get_all_reminders, set_reminder, reminders

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('', methods=['GET'])
def get_reminders():
    """Get all reminders"""
    return jsonify(get_all_reminders())

@reminders_bp.route('', methods=['POST'])
def create_reminder():
    """Create a new reminder"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    title = data.get('title')
    date = data.get('date')
    time = data.get('time')
    description = data.get('description')
    
    if not title or not date or not time:
        return jsonify({"error": "Title, date, and time are required"}), 400
    
    result = set_reminder(title, date, time, description)
    
    if result.get('success'):
        return jsonify(result.get('reminder')), 201
    else:
        return jsonify({"error": result.get('message')}), 400

@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """Delete a reminder by ID"""
    # Find the reminder with the given ID
    for i, reminder in enumerate(reminders):
        if reminder['id'] == reminder_id:
            # Remove the reminder from the list
            deleted_reminder = reminders.pop(i)
            return jsonify({"message": f"Reminder '{deleted_reminder['title']}' deleted successfully"})
    
    return jsonify({"error": f"Reminder with ID {reminder_id} not found"}), 404 