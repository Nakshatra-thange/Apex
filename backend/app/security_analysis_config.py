# This file contains the rules and patterns for our mock security scanner.

# ==============================================================================
# 1. Patterns for Common Vulnerabilities (using Regular Expressions)
# ==============================================================================
VULNERABILITY_PATTERNS = {
    "HARDCODED_SECRET": [
        # Looks for variable assignments with common secret names and string literals
        r'(api_key|secret|password|token)\s*=\s*["\'][a-zA-Z0-9_]{16,}["\']'
    ],
    "SQL_INJECTION": [
        # A very basic check for f-string formatting in common SQL commands
        r'f"SELECT.*FROM.*WHERE.*\{.*\}',
        r'f"UPDATE.*SET.*WHERE.*\{.*\}',
        r'f"DELETE.*FROM.*WHERE.*\{.*\}'
    ],
    "XSS_VULNERABILITY": [
        # Looks for dangerous assignments to innerHTML in JavaScript/TypeScript
        r'\.innerHTML\s*=\s*.*'
    ]
}

# ==============================================================================
# 2. Mock Database of Insecure Dependencies
# ==============================================================================
# This simulates a real vulnerability database like OSV or Snyk.
# We will check if the code imports a library with a known vulnerable version.
INSECURE_DEPENDENCIES = {
    # library_name: vulnerable_version
    "requests": "2.25.0",
    "insecure-lib": "1.0.1",
    "old-crypto-lib": "0.9.8"
}