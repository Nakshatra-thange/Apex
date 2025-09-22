import sys
import os
import hashlib
import json

# This allows the script to import modules from your backend app
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import set_cache, get_cache

# --- Mock Analysis Function ---
# In the real application, this would be our actual OpenAI analysis service.
# For now, it returns a fake, hardcoded review.
def mock_analyze_code(code_content: str, language: str) -> dict:
    """A mock function to simulate AI code analysis."""
    print(f"   -> Running MOCK analysis for {language} snippet...")
    # Simulate a delay
    import time
    time.sleep(2)
    return {
        "score": 85,
        "language": language,
        "suggestions": [
            {
                "type": "performance",
                "line": 1,
                "message": "This is a common boilerplate, no performance issues found."
            }
        ],
        "vulnerabilities": []
    }

# --- Cache Key Generation (copied from our design) ---
def create_review_cache_key(code_content: str, language: str, model_version="v1.0") -> str:
    """Generates a consistent cache key for a code snippet."""
    encoded_code = code_content.encode('utf-8')
    code_hash = hashlib.sha256(encoded_code).hexdigest()
    return f"apex:cache:review:{code_hash}:{language}:{model_version}"

# --- List of common code snippets to pre-load into the cache ---
COMMON_SNIPPETS = [
    {
        "language": "python",
        "content": "print('Hello, World!')"
    },
    {
        "language": "javascript",
        "content": "console.log('Hello, World!');"
    },
    {
        "language": "java",
        "content": 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}'
    }
]

def run_cache_warmer():
    print("🔥 Starting Cache Warmer...")
    warmed_count = 0
    skipped_count = 0

    for snippet in COMMON_SNIPPETS:
        lang = snippet["language"]
        code = snippet["content"]
        
        print(f"\nProcessing snippet for: {lang}")
        
        cache_key = create_review_cache_key(code, lang)
        
        # 1. Check if the cache key already exists
        if get_cache(cache_key):
            print("   ✅ Cache hit. Skipping.")
            skipped_count += 1
            continue
        
        # 2. If not, run the analysis
        print("   ⚠️ Cache miss. Warming now...")
        analysis_result = mock_analyze_code(code, lang)
        
        # 3. Store the result in the cache (TTL: 24 hours)
        set_cache(cache_key, analysis_result, ttl_seconds=86400)
        print("   ✅ Cache warmed successfully.")
        warmed_count += 1

    print(f"\n✨ Cache warming complete. Warmed: {warmed_count}, Skipped: {skipped_count}.")


if __name__ == "__main__":
    run_cache_warmer()

    