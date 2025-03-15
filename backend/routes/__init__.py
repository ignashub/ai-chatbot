from flask import Blueprint

# Create a main API blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

# This file makes the routes directory a Python package 