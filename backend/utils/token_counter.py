import tiktoken

def count_tokens(text, model="gpt-4"):
    """
    Count the number of tokens in a text string for a specific model.
    
    Args:
        text (str): The text to count tokens for
        model (str): The model to use for token counting (default: "gpt-4")
        
    Returns:
        int: Number of tokens
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text)) 