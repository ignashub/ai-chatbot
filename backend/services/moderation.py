import re
import base64
import os
import requests
from langchain_openai import ChatOpenAI
from urllib.parse import urlparse
import openai
import json
from typing import Tuple, List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

# Define blocklist for basic content filtering
BLOCKLIST = [
    # Offensive terms
    "offensive content",
    "hate speech",
    "explicit content",
    # Add more terms as needed
]

# List of trusted domains that should bypass strict moderation
TRUSTED_DOMAINS = [
    "gfmer.ch",  # Geneva Foundation for Medical Education and Research
    ".edu",      # Educational institutions
    ".ac.",      # Academic institutions
    "who.int",   # World Health Organization
    "nih.gov",   # National Institutes of Health
    "cdc.gov",   # Centers for Disease Control
    "bmj.com",   # British Medical Journal
    "nejm.org",  # New England Journal of Medicine
    "lancet.com" # The Lancet
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

def is_trusted_domain(url):
    """Check if the URL is from a trusted domain."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check if domain or any parent domain is in trusted list
        domain_parts = domain.split('.')
        for i in range(len(domain_parts) - 1):
            check_domain = '.'.join(domain_parts[i:])
            if check_domain in TRUSTED_DOMAINS:
                return True
            
        # Check for academic TLDs
        if domain.endswith('.edu') or domain.endswith('.ac.uk'):
            return True
            
        return False
    except:
        return False

def is_prompt_safe(prompt: Optional[str]) -> Tuple[bool, str]:
    """
    Check if a prompt is safe to process.
    
    Args:
        prompt: The prompt to check
        
    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the prompt is safe and a reason if it's not
    """
    # Handle None or empty prompts
    if prompt is None:
        return True, ""
    
    if not prompt.strip():
        return True, ""
    
    # Check if the prompt is a URL to a trusted domain
    if prompt.startswith("http"):
        for domain in TRUSTED_DOMAINS:
            if domain in prompt.lower():
                return True, ""
    
    # Basic content filtering
    for term in BLOCKLIST:
        if term.lower() in prompt.lower():
            return False, f"Inappropriate content detected: {term}"
    
    # Use OpenAI's moderation API for more sophisticated filtering
    try:
        response = client.moderations.create(input=prompt)
        result = response.results[0]
        
        if result.flagged:
            # Find the categories that were flagged
            flagged_categories = []
            for category, flagged in result.categories.model_dump().items():
                if flagged:
                    flagged_categories.append(category)
            
            if flagged_categories:
                return False, f"Inappropriate content detected by AI validation: {', '.join(flagged_categories)}"
        
        return True, ""
    except Exception as e:
        print(f"Error in moderation API: {str(e)}")
        # Fall back to basic filtering if the API call fails
        return True, "" 