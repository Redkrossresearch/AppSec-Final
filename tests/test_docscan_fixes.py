"""Regression safety net for the two docscan 'false assurance' fixes.

Ported from scratchpad/verify_docscan_fixes.py into permanent pytest form.
Tests only — no engine code under backend/services/docscan/ is imported for
mutation; these exercise the public seams and assert their contracts hold.

Covers:
1. Evidence-based confidence — a clean PDF with 20+ links is NOT high confidence,
   and confidence responds to real threat severity, not list length.
2. pikepdf sanitizer — a PDF armed with /OpenAction + /JavaScript + embedded file
   is disarmed, the output still opens in pikepdf, a re-scan shows the items gone,
   and the removal report lists them.
3. The {"type","value"} contract and adapter Finding mapping are unchanged, plus
   the sanitizer-unpack contract on summary["document"]["sanitized_file"].
"""
import os

import pikepdf
import pytest
from reportlab.pdfgen import canvas

from backend.services.docscan.intelligence.confidence_engine import confidence_score
from backend.services.docscan.sanitizers.pdf_sanitizer import sanitize_pdf
from backend.services.docscan.scanners.pdf_scanner import scan_pdf
from backend.services.docscan.adapter import scan_document

# Exactly the columns Finding(**item) expects — the load-bearing merge seam.
FINDING_KEYS = {
    "rule_id", "category", "severity", "title", "description", "file_path",
    "line_number", "line_text", "recommendation", "cvss_score", "fixable",
}


# --------------------------------------------------------------------------- #
# Helpers (ported verbatim from the verification script)
# --------------------------------------------------------------------------- #
def make_clean_pdf_with_links(path, n=25):
    """A benign PDF that is deliberately link-heavy — the confidence-inflation trap."""
    c = canvas.Canvas(path)
    y = 800
    for i in range(n):
        c.drawString(40, y, f"Visit http://example{i}.com/page for details")
        y -= 25
        if y < 40:
            c.showPage()
            y = 800
    c.showPage()
    c.save()


def make_armed_pdf(path):
    """A PDF armed structurally with /OpenAction + doc-level JS + an embedded file."""
    # Start from a trivial clean PDF, then arm it structurally with pikepdf.
    tmp = path + ".base.pdf"
    c = canvas.Canvas(tmp)
    c.drawString(72, 720, "hello")
    c.showPage()
    c.save()

    pdf = pikepdf.open(tmp)
    js = pdf.make_indirect(pikepdf.Dictionary(
        S=pikepdf.Name.JavaScript,
        JS="app.alert('pwned');",
    ))
    # Document open action.
    pdf.Root.OpenAction = js
    # Document-level JavaScript name tree.
    pdf.Root.Names = pikepdf.Dictionary(
        JavaScript=pikepdf.Dictionary(
            Names=pikepdf.Array([pikepdf.String("EvilOnOpen"), js])
        )
    )
    # Embedded file payload (creates /Names/EmbeddedFiles).
    pdf.attachments["evil.bin"] = b"MZ\x90\x00fake-payload"
    pdf.save(path)
    pdf.close()
    os.remove(tmp)


def root_has_active_content(path):
    """Re-scan structurally: is any dangerous key still reachable on the catalog?"""
    with pikepdf.open(path) as pdf:
        root = pdf.Root
        js_tree = False
        ef_tree = False
        if "/Names" in root:
            names = root.Names
            js_tree = "/JavaScript" in names
            ef_tree = "/EmbeddedFiles" in names
        return {
            "OpenAction": "/OpenAction" in root,
            "AA": "/AA" in root,
            "Names.JavaScript": js_tree,
            "Names.EmbeddedFiles": ef_tree,
        }


# --------------------------------------------------------------------------- #
# Fixtures (replacing the script's on-the-fly generation + PASS/FAIL counter)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def clean_pdf(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("docscan") / "clean_links.pdf")
    make_clean_pdf_with_links(path, n=25)
    return path


@pytest.fixture(scope="session")
def armed_pdf(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("docscan") / "armed.pdf")
    make_armed_pdf(path)
    return path


@pytest.fixture(scope="session")
def clean_findings(clean_pdf):
    return scan_pdf(clean_pdf)


@pytest.fixture(scope="session")
def armed_sanitize(armed_pdf, tmp_path_factory):
    out_dir = str(tmp_path_factory.mktemp("armed_sanitized"))
    return sanitize_pdf(armed_pdf, output_folder=out_dir)


@pytest.fixture(scope="session")
def clean_sanitize(clean_pdf, tmp_path_factory):
    out_dir = str(tmp_path_factory.mktemp("clean_sanitized"))
    return sanitize_pdf(clean_pdf, output_folder=out_dir)


@pytest.fixture(scope="session")
def scanned_document(request, tmp_path_factory):
    """scan_document() result for the named doc ('clean' or 'armed')."""
    path = request.getfixturevalue(f"{request.param}_pdf")
    out_dir = str(tmp_path_factory.mktemp(f"{request.param}_docscan"))
    return scan_document(path, sanitized_dir=out_dir)


# --------------------------------------------------------------------------- #
# 1. Evidence-based confidence
# --------------------------------------------------------------------------- #
def test_confidence_thirty_urls_not_inflated():
    findings = [{"type": "File Name", "value": "x"}, {"type": "SHA256", "value": "y"}]
    findings += [{"type": "URL", "value": f"http://e{i}.com"} for i in range(30)]
    assert confidence_score(findings) == "15%"


def test_confidence_single_payload_is_high():
    assert int(confidence_score([{"type": "Payload", "value": "x"}]).rstrip("%")) >= 90


def test_confidence_single_suspicious_api_is_medium():
    assert confidence_score([{"type": "Suspicious API", "value": "x"}]) == "55%"


def test_confidence_empty_is_low():
    assert confidence_score([]) == "15%"


def test_clean_pdf_confidence_is_low_band(clean_findings):
    conf = next((f["value"] for f in clean_findings if f["type"] == "Confidence"), None)
    assert conf == "15%"


def test_clean_pdf_carries_many_urls(clean_findings):
    urls_found = next(
        (f["value"] for f in clean_findings if f["type"] == "URLs Found"), 0
    )
    assert int(urls_found) >= 20


# --------------------------------------------------------------------------- #
# 2. pikepdf sanitizer disarms + proves it
# --------------------------------------------------------------------------- #
def test_armed_pdf_has_open_action(armed_pdf):
    assert root_has_active_content(armed_pdf)["OpenAction"]


def test_armed_pdf_has_doc_level_javascript(armed_pdf):
    assert root_has_active_content(armed_pdf)["Names.JavaScript"]


def test_armed_pdf_has_embedded_file(armed_pdf):
    assert root_has_active_content(armed_pdf)["Names.EmbeddedFiles"]


def test_sanitize_report_lists_open_action_removal(armed_sanitize):
    assert any("OpenAction" in r for r in armed_sanitize["removed"])


def test_sanitize_report_lists_javascript_removal(armed_sanitize):
    assert any("JavaScript" in r or "/JS" in r for r in armed_sanitize["removed"])


def test_sanitize_report_lists_embedded_file_removal(armed_sanitize):
    assert any("EmbeddedFiles" in r or "/EF" in r for r in armed_sanitize["removed"])


def test_sanitized_output_path_exists(armed_sanitize):
    out_file = armed_sanitize["output_file"]
    assert out_file and os.path.exists(out_file)


def test_sanitized_output_opens_in_pikepdf(armed_sanitize):
    with pikepdf.open(armed_sanitize["output_file"]):
        pass  # opening without exception is the assertion


def test_sanitized_output_open_action_gone(armed_sanitize):
    assert not root_has_active_content(armed_sanitize["output_file"])["OpenAction"]


def test_sanitized_output_javascript_gone(armed_sanitize):
    assert not root_has_active_content(armed_sanitize["output_file"])["Names.JavaScript"]


def test_sanitized_output_embedded_files_gone(armed_sanitize):
    assert not root_has_active_content(armed_sanitize["output_file"])["Names.EmbeddedFiles"]


def test_clean_pdf_still_valid_after_sanitize(clean_sanitize):
    with pikepdf.open(clean_sanitize["output_file"]) as p:
        assert len(p.pages) >= 1


def test_clean_pdf_removes_nothing(clean_sanitize):
    assert clean_sanitize["removed"] == []


# --------------------------------------------------------------------------- #
# 3. Contract + adapter mapping unchanged
# --------------------------------------------------------------------------- #
def test_scan_pdf_returns_type_value_entries(clean_findings):
    assert all(set(e.keys()) == {"type", "value"} for e in clean_findings)


@pytest.mark.parametrize("scanned_document", ["clean", "armed"], indirect=True)
def test_findings_have_exact_finding_keys(scanned_document):
    findings = scanned_document["findings"]
    assert all(set(f.keys()) == FINDING_KEYS for f in findings)


@pytest.mark.parametrize("scanned_document", ["clean", "armed"], indirect=True)
def test_findings_category_is_document(scanned_document):
    findings = scanned_document["findings"]
    assert all(f["category"] == "document" for f in findings)


@pytest.mark.parametrize("scanned_document", ["clean", "armed"], indirect=True)
def test_findings_are_not_fixable(scanned_document):
    findings = scanned_document["findings"]
    assert all(f["fixable"] is False for f in findings)


@pytest.mark.parametrize("scanned_document", ["clean", "armed"], indirect=True)
def test_summary_has_document_block(scanned_document):
    assert "document" in scanned_document["summary"]


def test_clean_summary_confidence_is_low_band(clean_pdf, tmp_path):
    # Confidence low-band applies to the clean doc specifically (not the armed one).
    result = scan_document(clean_pdf, sanitized_dir=str(tmp_path / "sanitized"))
    assert result["summary"]["document"].get("confidence") == "15%"


@pytest.mark.parametrize("scanned_document", ["clean", "armed"], indirect=True)
def test_summary_sanitized_file_is_str_or_none(scanned_document):
    """Guards the sanitizer-unpack contract: the report is unpacked to a path (or
    None), never stored as the raw {"output_file", "removed"} dict."""
    sanitized_file = scanned_document["summary"]["document"].get("sanitized_file")
    assert isinstance(sanitized_file, (str, type(None)))
    assert not isinstance(sanitized_file, dict)
