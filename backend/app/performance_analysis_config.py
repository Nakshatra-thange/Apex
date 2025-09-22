# This file contains the rules and patterns for our mock performance scanner.

# ==============================================================================
# Performance Anti-Patterns (using Regular Expressions)
# ==============================================================================
# Each key represents a type of performance issue, and the value is a list of
# regex patterns to detect it.

PERFORMANCE_PATTERNS = {
    "INEFFICIENT_LOOP_CONCATENATION": [
        # Looks for string concatenation (+=) inside a for/while loop.
        # Suggests using ''.join() instead.
        r'\s*for\s.*\s*:\s*.*\s*\+=\s*.*',
        r'\s*while\s.*\s*:\s*.*\s*\+=\s*.*',
    ],
    "POTENTIAL_N_PLUS_ONE_QUERY": [
        # A basic check for database queries being executed inside a loop.
        r'\s*for\s.*\s*:\s*.*\.(execute|query|get|find)\(.*\)',
        r'\s*while\s.*\s*:\s*.*\.(execute|query|get|find)\(.*\)',
    ],
    "INEFFICIENT_FILE_READ": [
        # Looks for reading an entire file into memory at once.
        # Suggests iterating over the file handle instead.
        r'\.readlines\(\)'
    ],
    "HIGH_COMPLEXITY_NESTED_LOOP": [
        # A simple heuristic to detect potentially O(n^2) or worse complexity
        # by looking for a loop inside another loop.
        r'\s*for\s.*\s*:\s*.*\s*for\s'
    ]
}

