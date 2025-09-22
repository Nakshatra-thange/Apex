import os
from dotenv import load_dotenv
import openai
from typing import Dict, Any

# Import our new prompt generator and the mock service for fallbacks
from .prompt_generator import generate_final_prompts
from .tasks import mock_openai_analysis 

# Load environment variables
load_dotenv()

# Get the API key from the .env file
api_key = os.getenv("OPENAI_API_KEY")

# Create an async client if the key exists
client = openai.AsyncOpenAI(api_key=api_key) if api_key else None

async def get_ai_analysis(
    code_content: str,
    language: str,
    analysis_results: Dict[str, Any] # <-- ADDED: Now takes all analysis data
) -> Dict[str, Any]:
    """
    Gets a code review analysis from the OpenAI API using dynamically generated,
    context-aware prompts.
    
    Falls back to the mock service if no API key is found or if the API call fails.
    """
    if not client:
        print("   -> [OpenAI Client] No API key found. Falling back to mock service.")
        return await mock_openai_analysis(code_content, language)

    try:
        # --- THIS IS THE NEW CORE LOGIC ---
        # 1. Generate the prompts using our new service
        system_prompt, user_prompt = generate_final_prompts(
            analysis_results=analysis_results,
            code_content=code_content,
            language=language
        )
        # --- END OF NEW LOGIC ---

        print(f"   -> [OpenAI Client] Sending request to GPT-3.5 Turbo for analysis...")
        
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="gpt-3.5-turbo",
            temperature=0.2,
        )
        
        response_content = chat_completion.choices[0].message.content
        print("   -> [OpenAI Client] Successfully received analysis from API.")
        
        return {"summary": response_content}

    except openai.APIError as e:
        print(f"   -> [OpenAI Client] ERROR: OpenAI API error occurred. Falling back to mock service. Details: {e}")
        return await mock_openai_analysis(code_content, language)
