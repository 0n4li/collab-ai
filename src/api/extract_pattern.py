import re

def extract_pattern(text, method):
    """
    Extract multiple-choice answers (A-J) from LLM responses with improved accuracy.
    
    Args:
        text (str): The LLM response text to parse
        
    Returns:
        str: The extracted answer letter (A-J) or "NONE" if no answer is found
    """
    # Clean and normalize text
    cleaned_text = ' '.join(text.split())
    
    # Split into sentences for better context analysis
    sentences = re.split(r'[.!?]\s+|\n+', cleaned_text)
    
    for sentence in reversed(sentences):
        sentence = sentence.strip()
        extraction, done = method(sentence)
        if done:
            return extraction
    
    return None

def _method_agreement(sentence):
    if "disagree" in sentence.lower():
        return "disagree", True
    elif "agree" in sentence.lower():
        return "agree", True
    return None, False

def extract_agreement(text):
    return extract_pattern(text, _method_agreement) or "unknown"