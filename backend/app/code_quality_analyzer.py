import re
from typing import List, Dict, Any
import ast # Abstract Syntax Tree - for smarter analysis

# Import the rules we just defined
from .code_quality_config import (
    NAMING_CONVENTION_PATTERNS,
    DOC_COVERAGE_THRESHOLDS,
    TECH_DEBT_WEIGHTS,
)

def check_naming_conventions(code_content: str) -> List[Dict[str, Any]]:
    """Checks for PEP 8 naming convention violations using regex."""
    findings = []
    lines = code_content.splitlines()
    for line_num, line in enumerate(lines, 1):
        for name_type, pattern in NAMING_CONVENTION_PATTERNS.items():
            match = re.search(pattern, line)
            if match and name_type == "CLASS_NAME" and match.group(1).isupper():
                continue # Skip all-caps constants for class names
            if match and name_type != "CLASS_NAME" and match.group(1).islower():
                continue # Skip valid snake_case
            
            # This is a simplified check and might have false positives.
            # A full linter would be more accurate.
            if match:
                findings.append({
                    "line": line_num,
                    "type": "NAMING_VIOLATION",
                    "description": f"Potential naming convention violation for {name_type.replace('_', ' ').lower()}: '{match.group(1)}'",
                })
    return findings

def analyze_documentation_coverage(code_content: str) -> Dict[str, Any]:
    """Analyzes documentation coverage using Python's Abstract Syntax Tree."""
    total_defs = 0
    defs_with_docstrings = 0
    missing_docstrings = []
    
    try:
        tree = ast.parse(code_content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                total_defs += 1
                if ast.get_docstring(node):
                    defs_with_docstrings += 1
                else:
                    missing_docstrings.append({
                        "line": node.lineno,
                        "type": "NO_DOCSTRING",
                        "description": f"Missing docstring for {node.name}",
                    })
    except SyntaxError:
        return {"coverage": 0.0, "rating": "poor", "findings": []} # Can't parse, so no coverage

    coverage = (defs_with_docstrings / total_defs * 100) if total_defs > 0 else 100.0
    
    rating = "poor"
    if coverage >= DOC_COVERAGE_THRESHOLDS["good"]:
        rating = "good"
    elif coverage >= DOC_COVERAGE_THRESHOLDS["medium"]:
        rating = "medium"
        
    return {"coverage": round(coverage, 2), "rating": rating, "findings": missing_docstrings}


def detect_code_duplication(code_content: str, min_lines: int = 4) -> List[Dict[str, Any]]:
    """A simple line-based code duplication detector."""
    findings = []
    lines = [line.strip() for line in code_content.splitlines() if line.strip()]
    
    hashes = {}
    for i in range(len(lines) - min_lines + 1):
        chunk = "".join(lines[i:i + min_lines])
        chunk_hash = hash(chunk)
        
        if chunk_hash in hashes:
            hashes[chunk_hash].append(i + 1)
        else:
            hashes[chunk_hash] = [i + 1]
    
    for _, line_numbers in hashes.items():
        if len(line_numbers) > 1:
            findings.append({
                "lines": line_numbers,
                "type": "DUPLICATED_LINE",
                "description": f"Duplicated block of {min_lines} lines found starting at lines: {', '.join(map(str, line_numbers))}",
            })
    return findings

def calculate_technical_debt(all_findings: List[Dict[str, Any]], complexity_score: int) -> int:
    """Calculates an estimated technical debt score in minutes."""
    total_debt = 0
    for finding in all_findings:
        total_debt += TECH_DEBT_WEIGHTS.get(finding["type"], 0)
    
    # Add debt for high complexity
    if complexity_score > 10: # Arbitrary threshold for high complexity
        total_debt += TECH_DEBT_WEIGHTS.get("HIGH_COMPLEXITY", 0)
        
    return total_debt


def run_code_quality_analysis(code_content: str, code_metrics: dict) -> Dict[str, Any]:
    """The main function that orchestrates the entire code quality scan."""
    print("   -> [Quality Module] Running static analysis...")
    
    naming_findings = check_naming_conventions(code_content)
    doc_analysis = analyze_documentation_coverage(code_content)
    duplication_findings = detect_code_duplication(code_content)
    
    all_findings = naming_findings + doc_analysis["findings"] + duplication_findings
    
    tech_debt = calculate_technical_debt(all_findings, code_metrics.get("cyclomatic_complexity", 0))
    
    report = {
        "issue_count": len(all_findings),
        "documentation": {"coverage": doc_analysis["coverage"], "rating": doc_analysis["rating"]},
        "technical_debt_minutes": tech_debt,
        "findings": all_findings
    }
    
    print(f"   -> [Quality Module] Scan complete. Found {len(all_findings)} issues.")
    
    return report