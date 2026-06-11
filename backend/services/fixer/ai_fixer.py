"""AI-powered code fixer using Claude API for any type of security issue."""
import json
import re
from typing import Optional

from flask import current_app

from backend.services.fixer.diff_generator import generate_diff
from backend.utils.file_helpers import read_text_safely
from backend.utils.validators import project_file

try:
    import anthropic
except ImportError:
    anthropic = None


def _get_code_context(content: str, line_number: Optional[int], context_lines: int = 5) -> str:
    """Extract code snippet around the issue with line numbers."""
    lines = content.split('\n')
    if not line_number or line_number < 1:
        return content
    
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)
    
    context_lines_list = []
    for i in range(start, end):
        marker = ">>> " if i == line_number - 1 else "    "
        context_lines_list.append(f"{marker}{i + 1:4d} | {lines[i]}")
    
    return "\n".join(context_lines_list)


def fix_with_ai(finding: dict, file_content: str, language: str = "python") -> Optional[dict]:
    """
    Use Claude API to generate a fix for any security finding.
    
    Args:
        finding: Dictionary with finding details (rule_id, category, title, description, line_number)
        file_content: The full file content as string
        language: Programming language (python, javascript, etc.)
    
    Returns:
        Dict with fixed_content, explanation, and diff, or None if fix failed
    """
    if not current_app.config.get("ENABLE_AI_FIXER"):
        return None
    
    api_key = current_app.config.get("CLAUDE_API_KEY")
    if not api_key:
        current_app.logger.warning("CLAUDE_API_KEY not set; AI fixer disabled")
        return None
    
    if anthropic is None:
        current_app.logger.warning("anthropic package not installed; AI fixer disabled")
        return None
    
    try:
        # Get code context around the issue
        code_context = _get_code_context(
            file_content, 
            finding.get("line_number"),
            context_lines=7
        )
        
        # Build the prompt for Claude
        prompt = f"""You are a security expert code fixer. A security vulnerability was found in {language} code.

VULNERABILITY DETAILS:
- Rule: {finding.get('rule_id')}
- Category: {finding.get('category')}
- Issue: {finding.get('title')}
- Description: {finding.get('description')}
- Recommendation: {finding.get('recommendation', 'Fix this security issue')}

CODE CONTEXT (line {finding.get('line_number')} marked with >>>):
```{language}
{code_context}
```

FULL FILE:
```{language}
{file_content}
```

Generate ONLY the fixed version of the ENTIRE file. Your response must be:
1. A valid {language} file that can be executed
2. Fix ONLY the security issue, preserve everything else exactly
3. Add necessary imports if needed
4. Return ONLY the code, no explanations

Start your response with triple backticks and end with triple backticks."""

        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=current_app.config.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=8000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the fixed code from response
        response_text = message.content[0].text
        
        # Try to extract code from markdown code block
        code_match = re.search(r'```(?:\w+)?\n(.*?)```', response_text, re.DOTALL)
        fixed_content = code_match.group(1) if code_match else response_text.strip()
        
        # Validate the fix is different
        if fixed_content.strip() == file_content.strip():
            current_app.logger.warning(f"AI fixer returned unchanged code for {finding.get('rule_id')}")
            return None
        
        # Generate diff
        diff = generate_diff(file_content, fixed_content, finding.get("file_path", "file"))
        
        return {
            "applicable": True,
            "explanation": f"AI-powered fix for {finding.get('title')}: {finding.get('recommendation')}",
            "original_content": file_content,
            "fixed_content": fixed_content,
            "diff": diff,
            "ai_generated": True
        }
    
    except Exception as e:
        current_app.logger.error(f"AI fixer failed: {str(e)}")
        return None


def build_ai_fix_preview(finding, project_root) -> dict:
    """
    Build a fix preview using AI for any finding type.
    Falls back to simple fixes for known patterns.
    """
    from backend.services.fixer.auto_fixer import build_fix_preview as build_pattern_fix
    
    try:
        target = project_file(project_root, finding.file_path)
        if not target.exists():
            return {"applicable": False, "explanation": "The referenced file no longer exists."}
        
        original = read_text_safely(target)
        language = _detect_language(target.suffix)
        
        # Try pattern-based fixer first (faster, more reliable for known patterns)
        pattern_fix = build_pattern_fix(finding, project_root)
        if pattern_fix.get("applicable"):
            return pattern_fix
        
        # Fall back to AI fixer for unknown issues
        finding_dict = {
            "rule_id": finding.rule_id,
            "category": finding.category,
            "title": finding.title,
            "description": finding.description,
            "recommendation": finding.recommendation,
            "line_number": finding.line_number,
            "file_path": finding.file_path,
        }
        
        ai_fix = fix_with_ai(finding_dict, original, language)
        return ai_fix or pattern_fix or {
            "applicable": False,
            "explanation": "Could not generate an automatic fix for this issue.",
        }
    
    except Exception as e:
        return {
            "applicable": False,
            "explanation": f"Error generating fix: {str(e)}",
        }


def _detect_language(file_extension: str) -> str:
    """Detect programming language from file extension."""
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".php": "php",
        ".go": "go",
        ".rb": "ruby",
        ".sh": "bash",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".sql": "sql",
    }
    return ext_to_lang.get(file_extension.lower(), "text")
