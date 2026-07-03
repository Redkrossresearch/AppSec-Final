"""Shared DeepSec docscan taxonomy: the one place that classifies a raw
``{"type","value"}`` label as a genuine threat indicator vs. scan-level metadata.

This is a **leaf module** — it imports nothing from ``backend.services.docscan`` so
that both ``adapter.py`` and ``intelligence/confidence_engine.py`` can depend on it
without creating an import cycle (``adapter`` already pulls in the scanners, which
pull in ``confidence_engine``). Keeping the taxonomy here means the threat-vs-metadata
distinction is defined exactly once and reused by everything that needs it.
"""

# DeepSec "type" labels that are genuine threat indicators -> (severity, cvss).
# Anything not listed here and not in METADATA_TYPES is treated as a low-severity
# indicator so no raw finding is silently dropped.
THREAT_TYPES = {
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
METADATA_TYPES = {
    "File Name", "Pages", "Paragraphs", "Slides", "Sheets", "Sheet",
    "Image Format", "Dimensions", "Color Mode", "Files Inside ZIP", "Contained File",
    "SHA256", "Metadata", "URLs Found", "Statistics", "Total Findings",
    "Risk Score", "Confidence", "Exploitability", "Threat Family",
    "MITRE Technique", "Attack Chain", "Reputation", "Executive Summary",
    "Sanitized File", "Text Found",
}

# The severity a raw type falls back to when it is neither a known threat nor
# metadata — mirrors adapter._make_finding's ("low", 3.0) default so confidence
# and the adapter agree on how to treat unknown labels.
DEFAULT_SEVERITY = "low"
