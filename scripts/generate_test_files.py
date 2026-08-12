"""
Generates two benign test files for demoing the two scan engines on the
hosted site:

  test_appsec_project.zip  -> upload as a Project, run a code Scan
  test_docscan_sample.pdf  -> upload to Doc Scan

Everything in both files is inert (no real payloads, no live callbacks,
no destructive code) -- the strings only exist to match the rule engine's
regexes / keyword lists, the same way an EICAR file matches an AV signature
without being a virus.

Usage:
    .venv\\Scripts\\python.exe scripts\\generate_test_files.py [output_dir]
"""

import io
import os
import sys
import zipfile

from PyPDF2 import PdfWriter


def build_zip(output_dir: str) -> str:
    app_py = '''\
import os
import sqlite3

# --- SEC002: fake AWS access key (not a real credential) ---
AWS_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"

# --- SEC003: fake GitHub token (not a real credential) ---
GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz01"


def run_report(cmd, user_id):
    # --- FUNC001: eval on external-shaped input ---
    result = eval(cmd)

    # --- INJ001: shell=True with string interpolation ---
    os.system("echo " + cmd)

    # --- INJ002: SQL built with an f-string instead of parameters ---
    conn = sqlite3.connect("app.db")
    conn.execute(f"SELECT * FROM users WHERE id = {user_id}")

    return result
'''

    requirements_txt = "\n".join(
        [
            "django==4.0.0",
            "flask==2.0.0",
            "requests==2.20.0",
            "pyyaml==5.3",
        ]
    )

    readme_md = (
        "# Test AppSec Project\n\n"
        "Synthetic project for exercising the code scanner's rule engine:\n"
        "AKIA-style AWS key, gh-style token, eval(), shell=True/os.system "
        "string concat, f-string SQL, and four out-of-date dependencies.\n"
        "No real credentials, no real vulnerable code paths -- pattern bait only.\n"
    )

    zip_path = os.path.join(output_dir, "test_appsec_project.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test_appsec_project/app.py", app_py)
        zf.writestr("test_appsec_project/requirements.txt", requirements_txt)
        zf.writestr("test_appsec_project/README.md", readme_md)

    return zip_path


def build_pdf(output_dir: str) -> str:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    # Real, valid /OpenAction /JavaScript entry -- harmless app.alert(),
    # the same construct pdf_scanner.py's detect_javascript() looks for.
    writer.add_js(
        "app.alert('DocScan test file - benign, no payload executed.');"
    )

    # Bait strings for payload_extractor / malware_signature_scanner /
    # yara_scanner / ioc_scanner, carried in PDF metadata so they land in
    # the raw (uncompressed) file bytes the scanners regex over.
    writer.add_metadata(
        {
            "/Title": "DocScan Benign Test Sample",
            "/Subject": (
                "sample strings: powershell -Command Get-Process ; "
                "cmd.exe /c echo test ; "
                "data:text/plain;base64,SGVsbG8gRG9jU2Nhbg== ; "
                "beacon 192.0.2.10"
            ),
            "/Producer": "AppSec-Final test fixture (non-malicious)",
        }
    )

    pdf_path = os.path.join(output_dir, "test_docscan_sample.pdf")
    with open(pdf_path, "wb") as f:
        writer.write(f)

    return pdf_path


def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    os.makedirs(output_dir, exist_ok=True)

    zip_path = build_zip(output_dir)
    pdf_path = build_pdf(output_dir)

    print(f"Wrote {zip_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
