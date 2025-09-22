import re
import hashlib
from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.util import ClassNotFound
from radon.complexity import cc_visit
from typing import Dict, Any

def normalize_code(code_content: str) -> str:
    """
    Normalizes code by removing comments and extra whitespace.
    This is crucial for creating a consistent hash for similarity detection.
    """
    # Simple regex to remove single-line comments (e.g., //, #)
    # This is a basic implementation and could be improved for block comments.
    code = re.sub(r'(#|//).*', '', code_content)
    # Remove all whitespace characters (spaces, tabs, newlines)
    code = re.sub(r'\s+', '', code)
    return code.strip().lower()

def detect_language(code_content: str, original_filename: str = None) -> str:
    """
    Detects the programming language of a code snippet using Pygments.
    """
    try:
        # First, try guessing from the filename if provided
        if original_filename:
            try:
                return get_lexer_by_name(original_filename).name
            except ClassNotFound:
                pass # Fallback to content guessing
        
        # Guess the lexer based on the code content
        lexer = guess_lexer(code_content)
        return lexer.name
    except ClassNotFound:
        # If Pygments can't guess, default to 'Text'
        return "Text"

def calculate_metrics(code_content: str) -> Dict[str, Any]:
    """
    Calculates various metrics for a code snippet.
    - Lines of Code (LOC)
    - Cyclomatic Complexity
    """
    try:
        # Calculate Lines of Code (non-empty lines)
        loc = len([line for line in code_content.splitlines() if line.strip()])
        
        # Calculate Cyclomatic Complexity using Radon
        # Note: This works best for Python. For other languages, it may be less accurate.
        complexity_blocks = cc_visit(code_content)
        total_complexity = sum(block.complexity for block in complexity_blocks)
        
        return {
            "loc": loc,
            "cyclomatic_complexity": total_complexity
        }
    except Exception:
        # If Radon fails (e.g., on a non-Python file), return safe defaults
        return {
            "loc": loc,
            "cyclomatic_complexity": 0
        }

def process_code_snippet(code_content: str, original_filename: str = None) -> Dict[str, Any]:
    """
    The main function that runs all preprocessing steps.
    """
    # 1. Calculate metrics on the original code
    metrics = calculate_metrics(code_content)
    
    # 2. Normalize the code for similarity hashing
    normalized_content = normalize_code(code_content)
    
    # 3. Create a hash of the normalized content
    normalized_hash = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    # 4. Detect the language
    detected_language = detect_language(code_content, original_filename)
    
    # 5. Combine all results into a single dictionary
    return {
        "loc": metrics["loc"],
        "cyclomatic_complexity": metrics["cyclomatic_complexity"],
        "normalized_hash": normalized_hash,
        "detected_language": detected_language
    }
