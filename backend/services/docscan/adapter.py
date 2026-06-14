"""Adapter: DeepSec document scanners -> AppSec's Finding-dict contract.

This is the single load-bearing seam of the merge (see MERGE_STRATEGY.md sec 2).
DeepSec's scanners each return a flat ``list[{"type": str, "value": Any}]`` mixing
real threat indicators (Payload, Shellcode, YARA Match, ...) with scan-level metadata
(File Name, SHA256, Risk Score, MITRE Technique, Executive Summary, ...).

``scan_document(path)`` wraps them behind exactly the contract AppSec's code scanner
already returns, so document scans ride the existing Scan -> Finding -> Report pipeline:

    {"findings": [<finding dict>, ...], "files_scanned": 1, "summary": {...}}

Each finding dict contains *exactly* the columns ``Finding(**item)`` expects:
    rule_id, category, severity, title, description, file_path,
    line_number, line_text, recommendation, cvss_score, fixable

Per the merge rules, every document finding is ``fixable=False`` (DeepSec sanitizes
documents, it does not code-fix them) and uses category ``"document"`` so it stays
clearly distinct from code findings.
"""
import re
from pathlib import Path

from backend.services.risk.risk_calculator import calculate_risk
from backend.services.docscan.scanners.pdf_scanner import scan_pdf
from backend.services.docscan.scanners.docx_scanner import scan_docx
from backend.services.docscan.scanners.xlsx_scanner import scan_xlsx
from backend.services.docscan.scanners.pptx_scanner import scan_pptx
from backend.services.docscan.scanners.image_scanner import scan_image
from backend.services.docscan.scanners.zip_scanner import scan_zip

CATEGORY = "document"
_MAX_LINE_TEXT = 500

# Extension -> DeepSec scanner entry point.
_DISPATCH = {
    ".pdf": scan_pdf,
    ".docx": scan_docx,
    ".xlsx": scan_xlsx,
    ".pptx": scan_pptx,
    ".zip": scan_zip,
    ".png": scan_image,
    ".jpg": scan_image,
    ".jpeg": scan_image,
    ".gif": scan_image,
    ".bmp": scan_image,
}

# DeepSec "type" labels that are genuine threat indicators -> (severity, cvss).
# Anything not listed here and not in _METADATA_TYPES is treated as a low-severity
# indicator so no raw finding is silently dropped.
_THREAT_TYPES = {
    "Payload": ("critical", 9.3),
    "Shellcode": ("critical", 9.5),
    "Shellcode Indicator": ("critical", 9.0),
    "Exploit Indicator": ("critical", 9.1),
    "Malware Signature": ("critical", 9.4),
    "YARA Match": ("critical", 9.2),
    "Embedded File": ("high", 8.2),
    "Embedded Object": ("high", 8.0),
    "Hidden Code": ("high", 8.4),
    "PowerShell Indicator": ("high", 8.1),
    "Persistence": ("high", 7.8),
    "Command": ("high", 7.6),
    "High Risk": ("high", 7.5),
    "Suspicious API": ("medium", 6.0),
    "Suspicious": ("medium", 5.5),
    "Suspicious Content": ("medium", 5.3),
    "Behavior": ("medium", 5.0),
    "URL": ("low", 3.5),
    "IP Address": ("low", 3.2),
}

# DeepSec "type" labels that are scan-level context, not individual findings.
# These are folded into the summary (and the threat-context block on each finding).
_METADATA_TYPES = {
    "File Name", "Pages", "Paragraphs", "Slides", "Sheets", "Sheet",
    "Image Format", "Dimensions", "Color Mode", "Files Inside ZIP", "Contained File",
    "SHA256", "Metadata", "URLs Found", "Statistics", "Total Findings",
    "Risk Score", "Confidence", "Exploitability", "Threat Family",
    "MITRE Technique", "Attack Chain", "Reputation", "Executive Summary",
    "Sanitized File", "Text Found",
}

# Metadata labels folded into each finding's description so the intelligence travels
# with the finding (MERGE_STRATEGY.md sec 5, step 9).
_CONTEXT_KEYS = ("Threat Family", "MITRE Technique", "Attack Chain", "Reputation")

# Metadata labels surfaced at the top of the nested summary["document"] block.
_SUMMARY_KEYS = (
    "File Name", "SHA256", "Threat Family", "MITRE Technique", "Attack Chain",
    "Reputation", "Risk Score", "Confidence", "Exploitability",
    "Executive Summary", "Sanitized File",
)


def _rule_id(type_label):
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(type_label)).strip("_").upper()
    return f"DOC-{slug}"[:80]


def _first(meta, key, default=None):
    values = meta.get(key)
    return values[0] if values else default


def _context_block(meta):
    parts = []
    for key in _CONTEXT_KEYS:
        value = _first(meta, key)
        if value not in (None, "", "Unknown", "None"):
            parts.append(f"{key}: {value}")
    return " | ".join(parts)


def _make_finding(type_label, value, filename, context, recommendation):
    severity, cvss = _THREAT_TYPES.get(type_label, ("low", 3.0))
    value_text = str(value)
    description = f"{type_label} detected in document. Indicator: {value_text}"
    if context:
        description = f"{description}\n\nThreat context: {context}"
    return {
        "rule_id": _rule_id(type_label),
        "category": CATEGORY,
        "severity": severity,
        "title": f"{type_label} in {filename}",
        "description": description,
        "file_path": filename,
        "line_number": None,
        "line_text": value_text[:_MAX_LINE_TEXT],
        "recommendation": recommendation,
        "cvss_score": cvss,
        "fixable": False,
    }


def _error_finding(value, filename):
    return {
        "rule_id": "DOC-SCAN-ERROR",
        "category": CATEGORY,
        "severity": "info",
        "title": f"Document scan error in {filename}",
        "description": f"The document scanner reported an error: {value}",
        "file_path": filename,
        "line_number": None,
        "line_text": str(value)[:_MAX_LINE_TEXT],
        "recommendation": "Verify the file is a valid, non-corrupt document and retry the scan.",
        "cvss_score": 0.0,
        "fixable": False,
    }


def scan_document(path):
    """Scan one document and return AppSec's scan-result contract.

    Returns ``{"findings": [...], "files_scanned": 1, "summary": {...}}``. Unsupported
    extensions yield a single info finding rather than raising, so the caller's request
    flow mirrors a normal (zero-threat) scan.
    """
    path = Path(path)
    filename = path.name
    scanner = _DISPATCH.get(path.suffix.lower())

    if scanner is None:
        findings = [{
            "rule_id": "DOC-UNSUPPORTED",
            "category": CATEGORY,
            "severity": "info",
            "title": f"Unsupported document type: {path.suffix or 'unknown'}",
            "description": (
                f"No document scanner is registered for '{path.suffix}'. "
                f"Supported types: {', '.join(sorted(_DISPATCH))}."
            ),
            "file_path": filename,
            "line_number": None,
            "line_text": "",
            "recommendation": "Upload a PDF, DOCX, XLSX, PPTX, ZIP or image file.",
            "cvss_score": 0.0,
            "fixable": False,
        }]
        summary = calculate_risk(findings)
        summary["document"] = {"file_name": filename, "supported": False}
        return {"findings": findings, "files_scanned": 1, "summary": summary}

    raw = scanner(str(path))

    # Partition the raw {"type","value"} stream into metadata vs. recommendations
    # vs. threat indicators, preserving repeats (e.g. many URLs) as lists.
    meta = {}
    recommendations = []
    threats = []
    error_value = None
    for entry in raw:
        type_label = entry.get("type")
        value = entry.get("value")
        if type_label == "Recommendation":
            recommendations.append(str(value))
        elif type_label == "Error":
            error_value = value
        elif type_label in _METADATA_TYPES:
            meta.setdefault(type_label, []).append(value)
        else:
            threats.append((type_label, value))

    context = _context_block(meta)
    rec_text = " ".join(recommendations).strip() or (
        "Document finding — not auto-fixable. Review and use the sanitized copy "
        "rather than the original."
    )

    findings = [
        _make_finding(type_label, value, filename, context, rec_text)
        for type_label, value in threats
    ]
    if error_value is not None:
        findings.append(_error_finding(error_value, filename))

    # Top-level summary stays shape-compatible with AppSec's code-scan summary
    # (total/critical/high/medium/low/max_cvss); DeepSec intelligence rides in a
    # nested "document" block consumed by the document-scan views (Phase 3).
    summary = calculate_risk(findings)
    document = {"file_name": filename, "supported": True}
    for key in _SUMMARY_KEYS:
        value = _first(meta, key)
        if value is not None:
            document[key.lower().replace(" ", "_")] = value
    if recommendations:
        document["recommendations"] = recommendations
    if error_value is not None:
        document["error"] = str(error_value)
    summary["document"] = document

    return {"findings": findings, "files_scanned": 1, "summary": summary}
