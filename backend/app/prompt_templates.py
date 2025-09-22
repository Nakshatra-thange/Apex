# This file contains versioned, modular prompt templates for interacting with the AI.

PROMPT_VERSION = "v1"

# ==============================================================================
# System Prompts (Defines the AI's Persona and Role)
# ==============================================================================
SYSTEM_PROMPTS = {
    "v1": (
        "You are Apex Reviewer, an expert AI code analysis assistant. "
        "Your task is to provide a final summary based on the results from static analysis tools. "
        "The user has already seen the detailed findings. Your response MUST be a valid JSON object. "
        "The JSON object should contain two keys: "
        '1. "summary": A concise (2-4 sentences) and helpful executive summary. '
        '2. "key_suggestions": A list of the top 3 most critical, actionable suggestions as strings. '
        "Do not include any text or formatting outside of the JSON object."
    )
}

# ==============================================================================
# User Prompts (The User's Request to the AI)
# ==============================================================================
USER_PROMPTS = {
    "v1": (
        "Please provide a JSON summary for the following {language} code snippet, based on the static analysis results.\n\n"
        "### Static Analysis Results:\n"
        "- **Security Scan:** {security_issue_count} issues.\n"
        "- **Performance Scan:** {performance_issue_count} issues.\n"
        "- **Quality Scan:** {quality_issue_count} issues.\n"
        "- **Technical Debt:** {tech_debt_minutes} minutes.\n\n"
        "### Code Snippet:\n"
        "```\n"
        "{code_content}\n"
        "```"
    )
}
