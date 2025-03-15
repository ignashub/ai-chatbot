#!/usr/bin/env python
"""
Simple script to run the Flask app directly.
This helps bypass Python path issues.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    print("Starting AI Chatbot API server...")
    print("API will be available at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 