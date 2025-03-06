import re
import base64
import os
import requests
from langchain_openai import ChatOpenAI

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