# This file contains the rules and thresholds for our mock code quality analyzer.

# ==============================================================================
# 1. Naming Convention Patterns (using Regular Expressions for Python PEP 8)
# ==============================================================================
NAMING_CONVENTION_PATTERNS = {
    # Class names should be in PascalCase (e.g., MyClass)
    "CLASS_NAME": r'^\s*class\s+([A-Z][a-zA-Z0-9_]+)',
    
    # Function and method names should be in snake_case (e.g., my_function)
    "FUNCTION_NAME": r'^\s*def\s+([a-z_][a-z0-9_]+)',
    
    # Variable names (simple assignment) should be in snake_case
    "VARIABLE_NAME": r'^\s*([a-z_][a-z0-9_]+)\s*=',
}

# ==============================================================================
# 2. Documentation Coverage Thresholds
# ==============================================================================
# We will calculate the percentage of functions and classes that have docstrings.
# These thresholds define what we consider good, medium, or poor coverage.
DOC_COVERAGE_THRESHOLDS = {
    "good": 75.0,  # 75% or more is good
    "medium": 40.0 # 40% to 74% is medium
    # Anything below 40% is poor
}

# ==============================================================================
# 3. Technical Debt Calculation Weights
# ==============================================================================
# Assign a "cost" in minutes to each type of issue found.
# This allows us to calculate an estimated technical debt score.
TECH_DEBT_WEIGHTS = {
    "NAMING_VIOLATION": 5,      # 5 minutes to fix a bad name
    "NO_DOCSTRING": 15,         # 15 minutes to write a missing docstring
    "HIGH_COMPLEXITY": 30,      # 30 minutes to refactor a complex function
    "DUPLICATED_LINE": 3,       # 3 minutes for each duplicated line
}
