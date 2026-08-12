"""Render docs/feature_inventory.md to docs/feature_inventory.pdf.

Reuses the layout engine in render_report.py (styles, markdown parser, table sizing,
TOC and page furniture) so there is exactly one PDF renderer in the repo. Only the
source/output paths, the cover page and the footer label differ.

Usage:
    .venv\\Scripts\\python.exe scripts\\render_features.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

import render_report as rr

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE = BASE_DIR / "docs" / "feature_inventory.md"
OUTPUT = BASE_DIR / "docs" / "feature_inventory.pdf"

FOOTER = "AppSec Orchestrator — Feature Inventory"


class FeatureDoc(rr.ReportDoc):
    """Same layout as ReportDoc, with this document's own footer label."""

    def decorate(self, canvas, doc):
        if doc.page == 1:  # cover carries no furniture
            return
        canvas.saveState()
        canvas.setStrokeColor(rr.RULE)
        canvas.setLineWidth(0.4)
        canvas.line(rr.MARGIN, rr.MARGIN + 6, rr.PAGE_WIDTH - rr.MARGIN, rr.MARGIN + 6)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(rr.MUTED)
        canvas.drawString(rr.MARGIN, rr.MARGIN - 5, FOOTER)
        canvas.drawRightString(rr.PAGE_WIDTH - rr.MARGIN, rr.MARGIN - 5, f"Page {doc.page - 1}")
        canvas.restoreState()


def cover(styles):
    return [
        Spacer(1, 1.5 * inch),
        Paragraph("Feature Inventory", styles["title"]),
        Paragraph(
            "AppSec Orchestrator &mdash; every capability in the product, "
            "including minor ones",
            styles["subtitle"],
        ),
        Spacer(1, 0.35 * inch),
        HRFlowable(width="42%", thickness=2, color=rr.ACCENT, hAlign="LEFT"),
        Spacer(1, 0.35 * inch),
        Paragraph(
            "<b>163 features</b> across 17 subsystems &mdash; 38 REST endpoints, "
            "18 code detection rules, 19 document threat indicator types, "
            "6 document formats and 12 application pages.",
            styles["body"],
        ),
        Spacer(1, 0.5 * inch),
        Paragraph("Generated 1 August 2026", styles["meta"]),
        Paragraph("Branch <b>main</b> &middot; commit <b>8d3203f</b>", styles["meta"]),
        Paragraph(
            "Every count was derived from source, not from the repository's own "
            "documentation &mdash; see section 3.3.",
            styles["meta"],
        ),
    ]


def main():
    if not SOURCE.exists():
        print(f"ERROR: source not found: {SOURCE}", file=sys.stderr)
        return 1

    styles = rr.build_styles()
    markdown = SOURCE.read_text(encoding="utf-8")

    toc = TableOfContents()
    toc.levelStyles = [styles["toc1"], styles["toc2"]]
    toc.dotsMinLevel = 99

    story = cover(styles)
    story.append(PageBreak())
    story.append(Paragraph("Contents", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=rr.RULE, spaceAfter=8))
    story.append(toc)
    story.extend(rr.parse(markdown, styles))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = FeatureDoc(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=rr.MARGIN, rightMargin=rr.MARGIN,
        topMargin=rr.MARGIN, bottomMargin=rr.MARGIN + 16,
        title="AppSec Orchestrator — Feature Inventory",
        author="AppSec Orchestrator",
        subject="Complete enumeration of product features",
    )
    doc.multiBuild(story)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Wrote {OUTPUT}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
