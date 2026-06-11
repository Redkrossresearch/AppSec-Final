from difflib import unified_diff


def generate_diff(original, fixed, relative_path):
    return "".join(
        unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )
