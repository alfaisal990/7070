import re

# Prompt Injection detection signatures (case-insensitive)
INJECTION_PATTERNS = [
    # 1. Instruction overrides
    r"ignore\s+(?:previous|above|the)?\s*instructions",
    r"ignore\s+your\s*system",
    r"bypass\s+restrictions",
    r"override\s+system\s*instructions",
    r"forget\s+(?:everything|previous\s+instructions)",
    r"instead\s+of\s+following",
    r"new\s+rule:",
    # 2. System prompt extraction
    r"reveal\s+(?:your|the)?\s*system\s*(?:prompt|instructions)",
    r"output\s+your\s*(?:initial|system)?\s*(?:prompt|instructions)",
    r"print\s+your\s*(?:system|initial)?\s*(?:prompt|instructions)",
    r"what\s+is\s+your\s*system\s*(?:prompt|instructions)",
    r"what\s+are\s+your\s*system\s*(?:prompt|instructions)",
    # 3. Common jailbreaks
    r"\bdan\s+mode\b",
    r"\bdo\s+anything\s+now\b",
    r"\bjailbreak\b",
]

def is_prompt_injection(text: str) -> bool:
    """
    Checks if the given text contains prompt injection or instruction override signatures.
    Returns True if an injection attempt is detected, False otherwise.
    """
    if not text:
        return False
        
    text_lower = text.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
            
    return False
