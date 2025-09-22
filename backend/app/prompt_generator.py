from typing import Dict, Any, Tuple

# Import our versioned templates
from .prompt_templates import PROMPT_VERSION, SYSTEM_PROMPTS, USER_PROMPTS

def generate_final_prompts(
    analysis_results: Dict[str, Any],
    code_content: str,
    language: str
) -> Tuple[str, str]:
    """
    Generates the final system and user prompts based on the active template version
    and the results from the static analysis pipeline.

    Args:
        analysis_results: The combined dictionary containing all analysis reports.
        code_content: The original code snippet.
        language: The detected programming language.

    Returns:
        A tuple containing the (system_prompt, user_prompt).
    """
    # 1. Select the active prompt version from our config
    active_version = PROMPT_VERSION
    
    system_prompt = SYSTEM_PROMPTS.get(active_version)
    user_prompt_template = USER_PROMPTS.get(active_version)

    if not system_prompt or not user_prompt_template:
        raise ValueError(f"Prompt version '{active_version}' not found in templates.")

    # 2. Extract the necessary context from the analysis results
    # We use .get() with defaults to make this robust against missing data.
    context = {
        "language": language,
        "code_content": code_content,
        "security_issue_count": analysis_results.get("security_report", {}).get("vulnerability_count", 0),
        "performance_issue_count": analysis_results.get("performance_report", {}).get("issue_count", 0),
        "quality_issue_count": analysis_results.get("quality_report", {}).get("issue_count", 0),
        "doc_coverage": analysis_results.get("quality_report", {}).get("documentation", {}).get("coverage", 0.0),
        "tech_debt_minutes": analysis_results.get("quality_report", {}).get("technical_debt_minutes", 0),
    }

    # 3. Format the user prompt template with the extracted context
    final_user_prompt = user_prompt_template.format(**context)

    return system_prompt, final_user_prompt