import re

def extract_answer(text):
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
    
    # Ordered by most common patterns first
    answer_patterns = [
        # Markdown and structured formats
        r"[Aa]nswer\s+is:?\s*\(?([A-J])\)",
        r"[Aa]nswer\s+is:?\s*\\\(\s*\\text\{\(([A-J])\)[^\)]*\}",
        r"\*\*(?:Correct\s+)?[Aa]nswer(?:\s+is)?:?\*\*\s*\(?([A-J])\)?",
        r"###\s*(?:Correct\s+)?[Aa]nswer:?\s*\(?([A-J])\)?",
        
        # Explicit answer statements with context
        r"[Aa]nswer:.*?\(([A-J])\)",  # Handle "Answer: See explanation above. (F)"
        r"[Aa]nswer:.*?([A-J])\b",  # Alternative without parentheses
        r"(?:[Tt]he\s+)?(?:final\s+)?(?:answer|choice|solution|response)\s+(?:is|would be|:)\s*\(?([A-J])\)?",
        r"\b[Aa]nswer\s*(?::|is)?\s*\(?([A-J])\)?\b",
        
        # Process of elimination and exception patterns
        r"[Aa]ll\s+options?\s+except\s*\(([A-J])\)\b",  # Handle "All options except (K) contain errors"
        r"[Aa]ll\s+(?:the\s+)?options?\s+except\s*([A-J])\b",  # Alternative without parentheses
        r"[Ee]xcept\s+(?:for\s+)?\(?([A-J])\)?",
        r"[Oo]nly\s*\(?([A-J])\)?\s*(?:is\s+correct|does\s+not|contains?|has|shows?)",
        
        # Selection and conclusion statements
        r"(?:[Tt]he\s+)?most\s+appropriate\s+answer\s+would\s+be\s+(?:option\s*)?\(?([A-J])\)?",
        r"(?:points|leads)\s+to\s+(?:choice\s*)?\(?([A-J])\)?",
        r"(?:we|to)\s+select\s*\(?([A-J])\)?(?:\s*[,.]|$)",
        r"[Tt]h(?:is|at)\s+leads\s+us\s+to\s+conclude\s*\(?([A-J])\)?",
        r"[Tt]herefore,?\s*(?:the\s+)?(?:answer|choice|solution|we\s+select)?\s*(?:is|:)?\s*\(?([A-J])\)?",
        r"(?:we|this)\s+(?:can\s+)?(?:conclude|see|deduce)\s+that\s*\(?([A-J])\)?(?:\s+is\s+correct)?",
        
        # Process of elimination patterns
        r"(?:[Ll]eaving|[Ll]eaves)\s+us\s+with\s*\(?([A-J])\)?",
        r"[Bb]y\s+process\s+of\s+elimination[^A-J]*?(?:[A-J]\)\s*(?:No|×)[^A-J]*)*([A-J])\)?\s*(?:Yes|✓|←)",
        r"[Oo]ptions\s+[A-J]\s+through\s+[A-J]\s+(?:are|is)\s+incorrect,?\s+making\s*\(?([A-J])\)?",
        
        # Option-based statements
        r"(?:[Oo]ption|[Cc]hoice)\s*\(?([A-J])\)?\s+(?:is|represents|provides)\s+(?:the\s+)?(?:best|correct|optimal)",
        r"\(?([A-J])\)?\s+(?:is|represents)\s+(?:the\s+)?(?:best|correct|optimal|only)\s+(?:choice|answer|solution)",
        
        # Visual indicators
        r"[✓✔]\s*(?:[Oo]ption)?\s*\(?([A-J])\)?",
        r"←\s*\(?([A-J])\)?",
        r"\(?([A-J])\)?\s+(?:Yes|Correct)\s*[✓✔←]",
        
        # Analysis and reasoning patterns
        r"[Aa]fter\s+(?:careful\s+)?(?:analysis|calculation|consideration)[^A-J]*?\(?([A-J])\)?",
        r"[Bb]ased\s+on\s+(?:the|these|our)\s+(?:given\s+)?(?:conditions|analysis)[^A-J]*?\(?([A-J])\)?",
        r"[Aa]ccording\s+to\s+(?:the\s+)?(?:principle|paragraph)[^A-J]*?\(?([A-J])\)?",
        
        # Simple option statements (least specific, check last)
        r"\b(?:[Oo]ption|[Cc]hoice)\s*\(?([A-J])\)?(?:\s+[^A-J]+|$)",
        r"\(?([A-J])\)?\s+(?:is|provides|represents)(?:\s+[^A-J]+|$)",
        
        # Fallback patterns for edge cases
        r"[Aa]nswer:.*?\(([A-J])\)",  # Another try at "Answer: See explanation above. (F)"
        r"[Aa]ll.*?except.*?\(([A-J])\)",  # Another try at "All options except (K)"
    ]
    
    # Check each sentence for answer patterns
    for sentence in reversed(sentences):
        sentence = sentence.strip()  # Remove leading/trailing whitespace
        for pattern in answer_patterns:
            match = re.search(pattern, sentence, re.DOTALL)  # Add re.DOTALL to handle newlines
            if match:
                return match.group(1).upper()
    
    # Special handling for "None of the above" cases
    none_pattern = r"(?:answer|choice)\s+is\s*(?:none|neither)|(?:none|neither)\s+of\s+(?:the|these|those)\s+(?:above|options|choices)|none\s+of\s+these\s+(?:are|is)\s+correct"
    
    for sentence in reversed(sentences):
        if re.search(none_pattern, sentence.lower()):
            return "NONE"
    
    # If no match found after all patterns
    return None
