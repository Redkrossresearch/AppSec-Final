"""Evidence-based confidence for a document scan.

Confidence answers "how sure are we this document is malicious?", so it must be
driven by *genuine threat evidence* — not by how many entries happen to be in the
findings list. The previous implementation returned 95%/85%/70% purely from
``len(findings)``, which meant a benign PDF with 20+ URLs scored 95% because the
scanner appends metadata (File Name, SHA256, Metadata, per-URL entries, MITRE, ...)
to the same list before calling this.

The fix: classify each entry through the shared taxonomy, ignore metadata entirely,
and score by the **highest severity tier of real evidence present** (with only a
small bump for multiple top-tier indicators). This way volume of low-value signals
— e.g. 20 bare URLs, all severity "low" — can never reach a high band.
"""

from backend.services.docscan.taxonomy import (
    THREAT_TYPES,
    METADATA_TYPES,
    DEFAULT_SEVERITY,
)

# Types that are neither threats nor metadata but still must not count as evidence.
_NON_EVIDENCE_TYPES = {"Recommendation", "Error"}

# Highest-tier-wins bands. Order matters: first tier present decides the base band.
_TIER_ORDER = ("critical", "high", "medium", "low")
_TIER_BASE = {
    "critical": 90,
    "high": 80,
    "medium": 55,
    "low": 15,
}
# Per-extra top-tier indicator bump, and the ceiling it may reach.
_CRITICAL_BUMP = 2
_CRITICAL_CAP = 95


def _severity_of(type_label):
    """Return the severity tier for a raw ``type`` label, or None if it is not
    genuine threat evidence (metadata / recommendation / error)."""
    if type_label in METADATA_TYPES or type_label in _NON_EVIDENCE_TYPES:
        return None
    severity, _ = THREAT_TYPES.get(type_label, (DEFAULT_SEVERITY, None))
    return severity


def confidence_score(findings):
    """Compute a ``"NN%"`` confidence string from real threat evidence only.

    ``findings`` is DeepSec's raw ``list[{"type","value"}]`` (metadata included, as
    the scanner passes it). Metadata and recommendation/error entries are skipped;
    the remaining entries are bucketed by severity tier and the highest tier present
    sets the band.
    """
    tier_counts = {tier: 0 for tier in _TIER_ORDER}
    for entry in findings:
        severity = _severity_of(entry.get("type"))
        if severity in tier_counts:
            tier_counts[severity] += 1

    for tier in _TIER_ORDER:
        if tier_counts[tier]:
            score = _TIER_BASE[tier]
            if tier == "critical" and tier_counts["critical"] > 1:
                score = min(
                    _CRITICAL_CAP,
                    score + (tier_counts["critical"] - 1) * _CRITICAL_BUMP,
                )
            return f"{score}%"

    # No genuine evidence at all — the document looks clean.
    return f"{_TIER_BASE['low']}%"
