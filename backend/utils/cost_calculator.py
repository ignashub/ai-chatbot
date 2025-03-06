# OpenAI pricing (update these if prices change)
PRICING_PER_1000_TOKENS = {
    "gpt-4": 0.03,  # $0.03 per 1,000 tokens (input)
    "gpt-3.5-turbo": 0.002,  # $0.002 per 1,000 tokens (input)
}

def calculate_cost(input_tokens, output_tokens, model="gpt-4"):
    """
    Calculate the estimated cost of an API call based on token usage.
    
    Args:
        input_tokens (int): Number of input tokens
        output_tokens (int): Number of output tokens
        model (str): The model used (default: "gpt-4")
        
    Returns:
        float: Estimated cost in dollars
    """
    price_per_1k = PRICING_PER_1000_TOKENS.get(model, 0.03)  # Default GPT-4 pricing
    cost = ((input_tokens + output_tokens) / 1000) * price_per_1k
    return round(cost, 6)  # Round to 6 decimal places 