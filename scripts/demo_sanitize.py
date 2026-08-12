"""Live before/after demo of PDF sanitization.

Both the original and the sanitized PDF render as the *same* page on screen — that is
the whole point of the attack class, and it means a visual side-by-side proves nothing.
This script shows the difference where it actually lives: the PDF object model.

Usage:
    .venv\\Scripts\\python.exe scripts\\demo_sanitize.py [path/to/file.pdf]

Defaults to test-files/test_docscan_sample.pdf.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pikepdf

from backend.services.docscan.sanitizers.pdf_sanitizer import sanitize_pdf

DEFAULT_PDF = os.path.join("test-files", "test_docscan_sample.pdf")

# Keys worth calling out on screen — the active-content carriers the sanitizer targets.
WATCH_KEYS = ("/OpenAction", "/AA", "/JavaScript", "/JS", "/Launch", "/EmbeddedFiles", "/EF")


def rule(title):
    print()
    print("=" * 68)
    print(f"  {title}")
    print("=" * 68)


def describe(path):
    """Print the parts of the object model that carry executable content."""
    with pikepdf.open(path) as pdf:
        print(f"  File            : {os.path.basename(path)}")
        print(f"  Size            : {os.path.getsize(path)} bytes")
        print(f"  /Root keys      : {[str(k) for k in pdf.Root.keys()]}")

        names = pdf.Root.get("/Names")
        print(f"  /Root/Names     : {'(absent)' if names is None else [str(k) for k in names.keys()] or '{} (empty)'}")

        # Walk every indirect object and count the dangerous keys still present.
        hits = []
        for obj in pdf.objects:
            if not isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream)):
                continue
            for key in obj.keys():
                if str(key) in WATCH_KEYS:
                    value = str(obj.get(key))
                    hits.append(f"{key} = {value[:60]}")

        if hits:
            print("  Active content  :")
            for hit in hits:
                print(f"      [!] {hit}")
        else:
            print("  Active content  : none found")

        page = pdf.pages[0]
        has_contents = "/Contents" in page
        print(f"  Page 1 /Contents: {'present' if has_contents else 'ABSENT (renders blank)'}")


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    if not os.path.isfile(source):
        print(f"No such file: {source}")
        return 1

    rule("BEFORE - original upload")
    describe(source)

    out_dir = os.path.join(tempfile.gettempdir(), "appsec_sanitize_demo")
    result = sanitize_pdf(source, out_dir)

    rule("SANITIZER REPORT - what was neutralized")
    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        return 1
    if result["removed"]:
        for item in result["removed"]:
            print(f"  [x] {item}")
    else:
        print("  (nothing removed — no active content was present)")

    rule("AFTER - sanitized copy")
    describe(result["output_file"])

    rule("RESULT")
    print(f"  Removed {len(result['removed'])} active-content item(s).")
    print(f"  {os.path.getsize(source)} bytes  ->  {os.path.getsize(result['output_file'])} bytes")
    print(f"  Safe copy: {result['output_file']}")
    print("\n  Note: both files render identically. Sanitization removes what")
    print("  *executes*, not what is visible.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
