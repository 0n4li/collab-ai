import re

from api.extract_pattern import extract_pattern

def _method_answer(sentence):
    
    # Special handling for "I cannot determine the answer" cases
    cannot_answer_pattern = r"i cannot determine the answer"
    
    if re.search(cannot_answer_pattern, sentence.lower()):
        return "IDK", True
    
    r_optional_the = r"(?:the\s+)?"
    r_optional_final = r"(?:final\s+|most\s+|only\s+)?"
    r_optional_correct = r"(?:correct\s+|appropriate\s+)?"
    r_answer = r"(?:answer|choice|solution|response|option)"
    r_optional_is = r"(?:\s+(?:is|would be|will be))?\s*"
    r_optional_colon = r"(?:\:+)?"
    r_optional_asterisk = r"(?:\**\s*)*"
    r_optional_parentheses_open = r"(?:\(\s*)?"
    r_optional_option = r"(?:option\s*)?"
    r_answer_range_match = r"\b([A-J])\b"
    r_optional_parentheses_close = r"(?:\s*\))?"
    r_optional_all = r"(?:all\s+)?"
    r_options = r"(?:answers|options|choices|solutions|responses)\s+"
    r_except = r"except\s+"
    
    match_answer_pattern = (
        rf'{r_optional_asterisk}'
        rf'{r_optional_parentheses_open}'
        rf'{r_optional_asterisk}'
        rf'{r_optional_option}'
        rf'{r_optional_asterisk}'
        rf'{r_answer_range_match}'
        rf'{r_optional_asterisk}'
        rf'{r_optional_parentheses_close}'
        rf'{r_optional_asterisk}'
    )
    
    # Ordered by most common patterns first
    answer_patterns = [
        # The answer is pattern
        rf"(?:the\s+)?(?:final\s+)?answer\s+is\s+{match_answer_pattern}",
        rf"(?:the\s+)?(?:final\s+)?answer\s+is\s+likely\s+to\s+be\s+{match_answer_pattern}",
        rf"(?:the\s+)?(?:final\s+)?answer.*is\s+{match_answer_pattern}",
    ]
    
    for pattern in answer_patterns:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(1).upper(), True
        
    error_patterns = [
        rf"an\s+unexpected\s+error\s+occurred",
    ]
    
    for pattern in error_patterns:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return "ERR", True
    
    # If no match found after all patterns
    return None, False
    
    
def extract_answer(text):
    return extract_pattern(text, _method_answer) or "NA"

