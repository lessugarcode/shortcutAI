"""
Right Click AI — Context Detector
Detects whether clipboard content is text, code, or image.
"""

import re
from typing import Literal


ContentType = Literal["text", "code", "image"]


# Common programming language indicators
CODE_PATTERNS = [
    # Function/method declarations
    r'\b(def|function|func|fn|void|int|string|bool|class|struct|enum|interface|impl)\b\s+\w+',
    # Common syntax patterns
    r'[{};]\s*$',
    r'^\s*(import|from|require|include|using|package)\s+',
    r'^\s*(if|else|elif|while|for|switch|case|try|catch|except)\s*[\({]',
    r'^\s*(return|yield|async|await)\s+',
    # Variable assignments with type hints or operators
    r'(const|let|var|val)\s+\w+\s*=',
    r'\w+\s*[=!<>]=\s*\w+',
    # Common code operators
    r'=>|->|\.\.|::|\|>',
    # HTML/XML tags
    r'<\/?[a-zA-Z][a-zA-Z0-9]*(\s[^>]*)?>',
    # Comments
    r'^\s*(//|#|/\*|\*|<!--)',
    # Brackets and semicolons density
    r'[\[\]{}()]+.*[\[\]{}()]+',
]

CODE_COMPILED = [re.compile(p, re.MULTILINE) for p in CODE_PATTERNS]


def detect_content_type(content: str, has_image: bool = False) -> ContentType:
    """
    Detect the type of content.
    
    Args:
        content: The text content to analyze
        has_image: Whether an image is present in the clipboard
    
    Returns:
        "image" if has_image, "code" if code-like, "text" otherwise
    """
    if has_image:
        return "image"
    
    if not content or not content.strip():
        return "text"
    
    # Check for code patterns
    code_score = 0
    lines = content.strip().split('\n')
    
    for pattern in CODE_COMPILED:
        if pattern.search(content):
            code_score += 1
    
    # Also check indentation patterns (common in code)
    indented_lines = sum(1 for line in lines if line.startswith('    ') or line.startswith('\t'))
    if len(lines) > 2 and indented_lines / len(lines) > 0.3:
        code_score += 2
    
    # Threshold: if 3+ patterns match, it's probably code
    if code_score >= 3:
        return "code"
    
    return "text"



