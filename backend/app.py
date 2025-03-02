import re
import base64
import os
import requests
import tiktoken  # OpenAI's token counter
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3002"}})

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# OpenAI pricing (update these if prices change)
PRICING_PER_1000_TOKENS = {
    "gpt-4": 0.03,  # $0.03 per 1,000 tokens (input)
    "gpt-3.5-turbo": 0.002,  # $0.002 per 1,000 tokens (input)
}

# Function to count tokens
def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Function to estimate cost
def calculate_cost(input_tokens, output_tokens, model="gpt-4"):
    price_per_1k = PRICING_PER_1000_TOKENS.get(model, 0.03)  # Default GPT-4 pricing
    cost = ((input_tokens + output_tokens) / 1000) * price_per_1k
    return round(cost, 6)  # Round to 6 decimal places

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

def ai_based_validation(prompt):
    """Use ChatGPT to evaluate the prompt for inappropriate content."""
    api_key = os.getenv('OPENAI_API_KEY')
    llm = ChatOpenAI(api_key=api_key, model_name="gpt-4")
    
    # More specific prompt for evaluating inappropriate content
    evaluation_prompt = (
        f"Please evaluate the following user input for inappropriate content, "
        f"including but not limited to profanity, hate speech, or any form of "
        f"abusive language. Examples of inappropriate content include words like 'damn', 'hell', "
        f"and any derogatory terms. Respond with 'inappropriate' if any such content is detected: {prompt}"
    )
    
    response = llm.invoke(evaluation_prompt)
    
    # Assuming the response contains a field indicating inappropriate content
    if "inappropriate" in response.content.lower():
        return False, "Inappropriate content detected by AI validation."
    
    return True, "Content is appropriate."

def is_prompt_safe(prompt):
    """Check if a prompt is safe using heuristic checks, keyword filtering, and OpenAI Moderation API."""
    
    # Strict keyword filtering (Immediate Block)
    for banned in BANNED_PHRASES:
        if banned in prompt.lower():
            return False, f"Blocked: '{banned}' is not allowed."
        
    # AI-based validation
    is_safe, message = ai_based_validation(prompt)
    if not is_safe:
        return False, message


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
    model = data.get('model', "gpt-4")  # Allow model selection
    temperature = data.get('temperature', 0.7)
    top_p = data.get('topP', 1.0)
    frequency_penalty = data.get('frequencyPenalty', 0.0)
    presence_penalty = data.get('presencePenalty', 0.0)
    api_key = os.getenv('OPENAI_API_KEY')

    # Check if message is safe
    is_safe, reason = is_prompt_safe(user_message)
    if not is_safe:
        return jsonify({'error': reason}), 403

    # Count input tokens
    input_tokens = count_tokens(f"{system_prompt}\n\nUser: {user_message}", model=model)

    # Initialize OpenAI
    llm = ChatOpenAI(api_key=api_key, model_name=model)

    # Generate response
    response = llm.invoke(
        f"{system_prompt}\n\nUser: {user_message}\nBot:",
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

    # Count output tokens
    output_tokens = count_tokens(response.content, model=model)

    # Calculate cost
    estimated_cost = calculate_cost(input_tokens, output_tokens, model)

    return jsonify({
        'response': response.content,
        'tokens': {
            'input': input_tokens,
            'output': output_tokens,
            'total': input_tokens + output_tokens
        },
        'estimated_cost': f"${estimated_cost}"
    })