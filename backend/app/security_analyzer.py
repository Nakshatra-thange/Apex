import re
from typing import List, Dict, Any

# Import the rules we just defined
from .security_analysis_config import VULNERABILITY_PATTERNS, INSECURE_DEPENDENCIES

def check_vulnerability_patterns(code_content: str) -> List[Dict[str, Any]]:
    """
    Scans code line-by-line against a dictionary of regex patterns.
    """
    findings = []
    lines = code_content.splitlines()
    
    for line_num, line in enumerate(lines, 1):
        for vuln_type, patterns in VULNERABILITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({
                        "line": line_num,
                        "type": vuln_type,
                        "description": f"Potential vulnerability found: {vuln_type.replace('_', ' ').title()}",
                        "snippet": line.strip()
                    })
    return findings

def check_insecure_dependencies(code_content: str) -> List[Dict[str, Any]]:
    """
    Scans code for import statements of known insecure libraries.
    This is a simplified check and would be more robust in a real application.
    """
    findings = []
    lines = code_content.splitlines()
    
    for line_num, line in enumerate(lines, 1):
        # Simple check for 'import library' or 'from library import'
        match = re.search(r'^(?:import|from)\s+([a-zA-Z0-9_.-]+)', line)
        if match:
            library_name = match.group(1)
            if library_name in INSECURE_DEPENDENCIES:
                findings.append({
                    "line": line_num,
                    "type": "INSECURE_DEPENDENCY",
                    "description": f"Use of potentially insecure library: '{library_name}'. Known vulnerable version: {INSECURE_DEPENDENCIES[library_name]}",
                    "snippet": line.strip()
                })
    return findings


def run_security_analysis(code_content: str) -> Dict[str, Any]:
    """
    The main function that orchestrates the entire security scan.
    """
    print("   -> [Security Module] Running static analysis...")
    
    # Run all our different checks
    pattern_findings = check_vulnerability_patterns(code_content)
    dependency_findings = check_insecure_dependencies(code_content)
    
    # Combine all the findings into a single list
    all_findings = pattern_findings + dependency_findings
    
    # Prepare the final report
    report = {
        "is_secure": len(all_findings) == 0,
        "vulnerability_count": len(all_findings),
        "findings": all_findings
    }
    
    print(f"   -> [Security Module] Scan complete. Found {len(all_findings)} potential issues.")
    
    return report