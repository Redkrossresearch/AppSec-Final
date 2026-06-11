import re

from backend.services.fixer.diff_generator import generate_diff
from backend.utils.file_helpers import add_import, read_text_safely
from backend.utils.validators import project_file


def _replace_line(content, line_number, transform):
    lines = content.splitlines(keepends=True)
    if not line_number or line_number > len(lines):
        return None
    updated = transform(lines[line_number - 1])
    if not updated or updated == lines[line_number - 1]:
        return None
    lines[line_number - 1] = updated
    return "".join(lines)


def _secret_fix(content, line_number):
    assignment = re.compile(
        r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([\"']).*?\3(\s*(?:#.*)?)(\r?\n)?$"
    )

    def transform(line):
        match = assignment.match(line)
        if not match:
            return None
        indent, variable, _quote, comment, newline = match.groups()
        env_name = variable.upper()
        return f'{indent}{variable} = os.getenv("{env_name}", ""){comment}{newline or ""}'

    updated = _replace_line(content, line_number, transform)
    return add_import(updated, "import os") if updated else None


def _eval_fix(content, line_number):
    def transform(line):
        return re.sub(r"\beval\s*\(", "ast.literal_eval(", line, count=1)

    updated = _replace_line(content, line_number, transform)
    return add_import(updated, "import ast") if updated else None


def build_fix_preview(finding, project_root):
    target = project_file(project_root, finding.file_path)
    if not target.exists():
        return {"applicable": False, "explanation": "The referenced file no longer exists."}
    original = read_text_safely(target)
    fixed = None
    explanation = ""
    if finding.rule_id == "SEC001" and target.suffix.lower() == ".py":
        fixed = _secret_fix(original, finding.line_number)
        explanation = "Move the Python secret assignment to an environment variable lookup."
    elif finding.rule_id == "FUNC001" and target.suffix.lower() == ".py":
        fixed = _eval_fix(original, finding.line_number)
        explanation = "Replace eval with ast.literal_eval for literal data parsing."
    else:
        return {
            "applicable": False,
            "explanation": "This issue needs a developer-reviewed change; an automatic rewrite could change behavior.",
        }
    if not fixed or fixed == original:
        return {
            "applicable": False,
            "explanation": "No safe mechanical replacement could be generated for this line.",
        }
    return {
        "applicable": True,
        "explanation": explanation,
        "original_content": original,
        "fixed_content": fixed,
        "diff": generate_diff(original, fixed, finding.file_path),
    }
