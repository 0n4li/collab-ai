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
    
    r_optional_the = r"(?:[Tt]he\s+)?"
    r_optional_final = r"(?:[Ff]inal\s+)?"
    r_optional_correct = r"(?:[Cc]orrect\s+)?"
    r_answer = r"(?:[Aa]nswer|[Cc]choice|[Ss]olution|[Rr]esponse)"
    r_optional_is = r"(?:\s+(?:is|would be|will be))?\s*"
    r_optional_colon = r"(?:\:+)?"
    r_optional_asterisk = r"(?:\**\s*)*"
    r_optional_parentheses_open = r"\(?"
    r_answer_range_match = r"\b([A-J]|[a-j])\b"
    r_optional_parentheses_close = r"\)?"
    
    main_pattern = (
        rf'{r_optional_asterisk}'
        rf'{r_optional_the}'
        rf'{r_optional_final}'
        rf'{r_optional_correct}'
        rf'{r_answer}'
        rf'{r_optional_colon}'
        rf'{r_optional_is}'
        rf'{r_optional_colon}'
        rf'{r_optional_asterisk}'
        rf'{r_optional_parentheses_open}'
        rf'{r_optional_asterisk}'
        rf'{r_answer_range_match}'
        rf'{r_optional_asterisk}'
        rf'{r_optional_parentheses_close}'
        rf'{r_optional_asterisk}'
    )
    
    #print(main_pattern)
    
    # Ordered by most common patterns first
    answer_patterns = [
        # Markdown and structured formats
        main_pattern,
        
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
