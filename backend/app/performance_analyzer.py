import re
from typing import List, Dict, Any

# Import the rules we just defined
from .performance_analysis_config import PERFORMANCE_PATTERNS

def check_performance_patterns(code_content: str) -> List[Dict[str, Any]]:
    """
    Scans code line-by-line against a dictionary of regex patterns for
    common performance anti-patterns.
    """
    findings = []
    lines = code_content.splitlines()
    
    for line_num, line in enumerate(lines, 1):
        # Skip empty or commented lines for efficiency
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith(('#', '//')):
            continue

        for issue_type, patterns in PERFORMANCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "line": line_num,
                        "type": issue_type,
                        "description": f"Potential performance issue found: {issue_type.replace('_', ' ').title()}",
                        "snippet": stripped_line
                    })
                    # Break after first match for a given line to avoid duplicate issue types
                    break 
    return findings


def run_performance_analysis(code_content: str) -> Dict[str, Any]:
    """
    The main function that orchestrates the entire performance scan.
    """
    print("   -> [Performance Module] Running static analysis...")
    
    # Run our pattern-matching check
    pattern_findings = check_performance_patterns(code_content)
    
    # In the future, other checks (e.g., memory profiling) could be added here.
    
    # Prepare the final report
    report = {
        "issue_count": len(pattern_findings),
        "findings": pattern_findings
    }
    
    print(f"   -> [Performance Module] Scan complete. Found {len(pattern_findings)} potential issues.")
    
    return report