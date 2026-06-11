from pathlib import Path


def read_text_safely(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text(encoding="utf-8", errors="replace")


def atomic_write_text(path, content):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".appsec.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def add_import(content, import_line):
    lines = content.splitlines(keepends=True)
    if any(line.strip() == import_line for line in lines):
        return content
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if insert_at < len(lines) and lines[insert_at].startswith(('"""', "'''")):
        quote = lines[insert_at][:3]
        insert_at += 1
        while insert_at < len(lines) and quote not in lines[insert_at]:
            insert_at += 1
        insert_at = min(insert_at + 1, len(lines))
    lines.insert(insert_at, f"{import_line}\n")
    return "".join(lines)
