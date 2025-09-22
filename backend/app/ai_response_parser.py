import json
from typing import Dict, Any

def parse_ai_response(response_content: str) -> Dict[str, Any]:
    """
    Parses the JSON response from the AI and validates its structure.
    If parsing fails, it returns a safe, default structure.
    """
    try:
        # Attempt to parse the string as JSON
        data = json.loads(response_content)
        
        # Validate that the expected keys are present
        if "summary" in data and "key_suggestions" in data and isinstance(data["key_suggestions"], list):
            # The response is valid and well-formed
            return data
        else:
            # The JSON is valid, but missing required keys
            raise ValueError("AI response JSON is missing required keys.")
            
    except (json.JSONDecodeError, ValueError) as e:
        print(f"   -> [Parser] WARNING: Could not parse or validate AI response. Error: {e}")
        # --- Fallback Mechanism ---
        # If the AI response is not valid JSON or is malformed,
        # we create a default summary using the raw text.
        return {
            "summary": response_content, # Use the raw response as the summary
            "key_suggestions": [],
            "parsing_error": str(e) # Log the error for monitoring
        }