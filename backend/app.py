from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import requests
import re
import base64
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3002"}})

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Banned phrases
BANNED_PHRASES = [
    "jailbreak", "bypass", "ignore previous instructions", "simulate", 
    "pretend", "act as", "hacked version", "developer mode"
]

# Suspicious patterns for heuristic checks
PATTERN_RULES = [
    re.compile(r"(ignore\s+all\s+previous\s+instructions)", re.IGNORECASE),  # Direct jailbreak
    re.compile(r"(\b(?:base64|hex|binary|encoded)\b)", re.IGNORECASE),  # Encoding hints
    re.compile(r"([a-zA-Z0-9+/]{20,}={0,2})"),  # Base64 encoded text detection
    re.compile(r"([^\w\s]{5,})"),  # Excessive special characters
    re.compile(r"(\bplease\b.*\bforget\b.*\bprevious\b.*\binstruction\b)", re.IGNORECASE),  # Prompt injections
]

def detect_encoded_jailbreak(prompt):
    """Detect if the prompt contains base64-encoded or hex-encoded jailbreak attempts."""
    try:
        decoded_text = base64.b64decode(prompt).decode('utf-8')
        if any(word in decoded_text.lower() for word in BANNED_PHRASES):
            return True
    except Exception:
        pass  # Not a valid base64 string, ignore
    
    try:
        decoded_hex = bytes.fromhex(prompt).decode('utf-8')
        if any(word in decoded_hex.lower() for word in BANNED_PHRASES):
            return True
    except Exception:
        pass  # Not a valid hex string, ignore
    
    return False

def is_prompt_safe(prompt):
    """Check if a prompt is safe using heuristic checks, keyword filtering, and OpenAI Moderation API."""
    
    # Strict keyword filtering (Immediate Block)
    for banned in BANNED_PHRASES:
        if banned in prompt.lower():
            return False, f"Blocked: '{banned}' is not allowed."

    # Pattern-based heuristic checks
    for pattern in PATTERN_RULES:
        if pattern.search(prompt):
            return False, "Blocked: Suspicious pattern detected."

    # Detect encoded jailbreak attempts
    if detect_encoded_jailbreak(prompt):
        return False, "Blocked: Encoded jailbreak attempt detected."

    # OpenAI Moderation API check
    api_key = os.getenv('OPENAI_API_KEY')
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(
        "https://api.openai.com/v1/moderations",
        json={"input": prompt},
        headers=headers
    )

    if response.status_code == 200:
        results = response.json()
        if results.get("results", [{}])[0].get("flagged", False):
            return False, "Blocked due to policy violations."

    return True, "Safe"

@app.route('/chat', methods=['OPTIONS', 'POST'])
@limiter.limit("10 per minute")  # Limit to 10 requests per minute per IP
def chat():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.json
    user_message = data.get('message')
    system_prompt = data.get('systemPrompt', "You are a Health and Wellness Coach.")
    temperature = data.get('temperature', 0.7)
    top_p = data.get('topP', 1.0)
    frequency_penalty = data.get('frequencyPenalty', 0.0)
    presence_penalty = data.get('presencePenalty', 0.0)
    api_key = os.getenv('OPENAI_API_KEY')

    # Check if the message is safe
    is_safe, reason = is_prompt_safe(user_message)
    if not is_safe:
        return jsonify({'error': reason}), 403

    # Initialize OpenAI with the provided API key
    llm = ChatOpenAI(api_key=api_key)

    # Generate response using the LLM with the system prompt
    response = llm.invoke(
        f"{system_prompt}\n\nUser: {user_message}\nBot:",
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

    return jsonify({'response': response.content})