# This file contains versioned, modular prompt templates for interacting with the AI.

# ==============================================================================
# PROMPT VERSIONING
# ==============================================================================
# By versioning our prompts, we can easily test new ones (e.g., v2) while
# keeping the old ones for fallback or A/B testing.
# The active version is controlled by the PROMPT_VERSION variable.
PROMPT_VERSION = "v1"

# ==============================================================================
# System Prompts (Defines the AI's Persona and Role)
# ==============================================================================
SYSTEM_PROMPTS = {
    "v1": (
        "You are Apex Reviewer, an expert AI code analysis assistant. "
        "Your task is to provide a final, executive summary based on the results from static analysis tools. "
        "The user has already seen the detailed findings from these tools. "
        "Your summary should be concise (2-4 sentences), helpful, and written in professional, clear English. "
        "Focus on the most critical issues and provide actionable advice. Do not repeat the individual findings. "
        "Conclude with an overall assessment."
    )
}

# ==============================================================================
# User Prompts (The User's Request to the AI)
# ==============================================================================
# These are f-string templates that will be filled with context from our analysis.
USER_PROMPTS = {
    "v1": (
        "Please provide an executive summary for the following {language} code snippet, keeping in mind the static analysis results.\n\n"
        "### Code Snippet:\n"
        "```\n"
        "{code_content}\n"
        "```\n\n"
        "### Static Analysis Results:\n"
        "- **Security Scan:** {security_issue_count} potential issues found.\n"
        "- **Performance Scan:** {performance_issue_count} potential issues found.\n"
        "- **Quality Scan:** {quality_issue_count} potential issues found.\n"
        "- **Documentation Coverage:** {doc_coverage}%\n"
        "- **Estimated Technical Debt:** {tech_debt_minutes} minutes.\n\n"
        "### Your Summary:"
    )
}
