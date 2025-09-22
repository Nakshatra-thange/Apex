import os
from dotenv import load_dotenv
import openai
from typing import Dict, Any

from .prompt_generator import generate_final_prompts
from .mock_services import mock_openai_analysis
from .ai_response_parser import parse_ai_response

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.AsyncOpenAI(api_key=api_key) if api_key else None

async def get_ai_analysis(
    code_content: str, language: str, analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Gets and parses a code review analysis from the OpenAI API.
    """
    if not client:
        print("   -> [OpenAI Client] No API key found. Falling back to mock service.")
        return await mock_openai_analysis(code_content, language)

    try:
        system_prompt, user_prompt = generate_final_prompts(
            analysis_results=analysis_results, code_content=code_content, language=language
        )
        
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
        
        # --- PARSE THE RESPONSE ---
        parsed_response = parse_ai_response(response_content)
        return parsed_response
        # --- END OF PARSING ---

    except openai.APIError as e:
        print(f"   -> [OpenAI Client] ERROR: OpenAI API error occurred. Falling back to mock service. Details: {e}")
        return await mock_openai_analysis(code_content, language)
