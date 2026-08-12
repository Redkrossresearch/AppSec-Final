"""Render docs/project_report.md to docs/project_report.pdf.

Uses reportlab (already a project dependency via backend/services/reporter/pdf_generator.py),
so this needs no new package and no external binary.

The output is deliberately optimised for machine ingestion as well as human reading:
single-column linear flow, real selectable text, simple tables, and numbered sections.

Usage:
    .venv\\Scripts\\python.exe scripts\\render_report.py
"""
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE = BASE_DIR / "docs" / "project_report.md"
OUTPUT = BASE_DIR / "docs" / "project_report.pdf"

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 45
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

INK = colors.HexColor("#12212e")
MUTED = colors.HexColor("#5a6b78")
ACCENT = colors.HexColor("#0b7a5c")
RULE = colors.HexColor("#c9d4dc")
CODE_BG = colors.HexColor("#f2f5f7")
HEAD_BG = colors.HexColor("#e8eef2")


# --------------------------------------------------------------------------- styles

def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["body"] = ParagraphStyle(
        "body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5,
        leading=13.5, spaceAfter=7, alignment=TA_LEFT, textColor=INK,
    )
    styles["h1"] = ParagraphStyle(
        "h1", parent=styles["body"], fontName="Helvetica-Bold", fontSize=17,
        leading=21, spaceBefore=6, spaceAfter=10, textColor=INK,
    )
    styles["h2"] = ParagraphStyle(
        "h2", parent=styles["body"], fontName="Helvetica-Bold", fontSize=13.5,
        leading=17, spaceBefore=16, spaceAfter=7, textColor=INK,
    )
    styles["h3"] = ParagraphStyle(
        "h3", parent=styles["body"], fontName="Helvetica-Bold", fontSize=11,
        leading=14, spaceBefore=12, spaceAfter=5, textColor=ACCENT,
    )
    styles["h4"] = ParagraphStyle(
        "h4", parent=styles["body"], fontName="Helvetica-BoldOblique", fontSize=10,
        leading=13, spaceBefore=9, spaceAfter=4, textColor=INK,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet", parent=styles["body"], leftIndent=14, bulletIndent=3, spaceAfter=4,
    )
    styles["code"] = ParagraphStyle(
        "code", parent=styles["body"], fontName="Courier", fontSize=7.8, leading=10.2,
        leftIndent=8, spaceBefore=4, spaceAfter=8, textColor=INK,
    )
    styles["cell"] = ParagraphStyle(
        "cell", parent=styles["body"], fontSize=8, leading=10.5, spaceAfter=0,
    )
    styles["cellhead"] = ParagraphStyle(
        "cellhead", parent=styles["cell"], fontName="Helvetica-Bold",
    )
    styles["title"] = ParagraphStyle(
        "title", parent=styles["body"], fontName="Helvetica-Bold", fontSize=26,
        leading=31, spaceAfter=14, textColor=INK,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", parent=styles["body"], fontSize=12, leading=17,
        spaceAfter=10, textColor=MUTED,
    )
    styles["meta"] = ParagraphStyle(
        "meta", parent=styles["body"], fontSize=9, leading=13, textColor=MUTED,
    )
    styles["toc1"] = ParagraphStyle(
        "toc1", parent=styles["body"], fontName="Helvetica-Bold", fontSize=10.5,
        leading=15, spaceBefore=8,
    )
    styles["toc2"] = ParagraphStyle(
        "toc2", parent=styles["body"], fontSize=9.5, leading=13.5, leftIndent=16,
    )
    return styles


# ----------------------------------------------------------------------- inline text

def escape(text):
    """Escape the three characters ReportLab's mini-HTML parser cares about.

    This is the step backend/services/reporter/pdf_generator.py omits, which is why
    a finding containing '<' can break that generator. Do it before any markup is added.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    """Convert a markdown inline span to ReportLab markup. Escapes first, always.

    Code spans are lifted out before the emphasis passes run. Without that, a literal
    '**' inside backticks (e.g. `**item`) opens a <b> that the following real '**'
    closes across the </font> boundary, and ReportLab's parser rejects the overlap.
    """
    out = escape(text)

    spans = []

    def stash(match):
        spans.append(match.group(1))
        return f"\x00{len(spans) - 1}\x00"

    out = re.sub(r"`([^`]+)`", stash, out)

    # **bold**
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    # *italic* (single asterisk not adjacent to another)
    out = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", out)

    def restore(match):
        body = spans[int(match.group(1))]
        return f'<font face="Courier" size="8.4" backColor="#eef2f4">{body}</font>'

    return re.sub(r"\x00(\d+)\x00", restore, out)


# ---------------------------------------------------------------------------- tables

CELL_PAD = 12          # LEFTPADDING + RIGHTPADDING plus a little slack
MAX_MIN_SHARE = 0.30   # no single column may claim more than this as its minimum


def _widest_word(text, font, size):
    plain = text.replace("**", "").replace("*", "")
    return max((stringWidth(word, font, size) for word in plain.split()), default=0.0)


def unbreakable_width(text, bold=False):
    """Width of the widest single token, measured in the font it will actually render in.

    Words inside backticks render in Courier 8.4, everything else in Helvetica 8.
    Getting this right is what stops a column from being squeezed narrower than its
    own content, which forces Paragraph to break words mid-token ("SEC002" -> "SEC00"/"2")
    and makes the rendered text unsearchable.
    """
    body_font = "Helvetica-Bold" if bold else "Helvetica"
    widest = 0.0
    position = 0
    for match in re.finditer(r"`([^`]+)`", text):
        widest = max(widest, _widest_word(text[position:match.start()], body_font, 8))
        widest = max(widest, _widest_word(match.group(1), "Courier", 8.4))
        position = match.end()
    return max(widest, _widest_word(text[position:], body_font, 8))


def column_widths(rows):
    """Width per column: never narrower than its widest token, surplus shared by bulk."""
    count = len(rows[0])
    minimums, weights = [], []
    cap = CONTENT_WIDTH * MAX_MIN_SHARE

    for index in range(count):
        cells = [row[index] if index < len(row) else "" for row in rows]
        widest = max(
            unbreakable_width(cell, bold=(position == 0))
            for position, cell in enumerate(cells)
        )
        # Cap so one very long token cannot starve every other column.
        minimums.append(min(widest + CELL_PAD, cap))
        average = sum(len(cell) for cell in cells) / max(len(cells), 1)
        weights.append(max(average, 6.0))

    total_minimum = sum(minimums)
    if total_minimum >= CONTENT_WIDTH:
        scale = CONTENT_WIDTH / total_minimum
        return [width * scale for width in minimums]

    surplus = CONTENT_WIDTH - total_minimum
    total_weight = sum(weights)
    return [
        minimums[index] + surplus * weights[index] / total_weight
        for index in range(count)
    ]


def make_table(rows, styles):
    header, body = rows[0], rows[1:]
    data = [[Paragraph(inline(c), styles["cellhead"]) for c in header]]
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        data.append([Paragraph(inline(c), styles["cell"]) for c in padded[: len(header)]])

    table = Table(data, colWidths=column_widths(rows), repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
                ("LINEBELOW", (0, 0), (-1, 0), 0.75, RULE),
                ("GRID", (0, 0), (-1, -1), 0.25, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafcfd")]),
            ]
        )
    )
    return table


def split_table_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def is_divider(line):
    return bool(re.fullmatch(r"\|?[\s:\-|]+\|?", line.strip())) and "-" in line


# ----------------------------------------------------------------------- code blocks

def make_code(lines, styles):
    """A fenced code block: wrapped in a tinted single-cell table so it reads as a unit."""
    text = "\n".join(lines) if lines else " "
    block = Preformatted(text, styles["code"], maxLineLength=110, splitChars=" ,.(){}[]/")
    holder = Table([[block]], colWidths=[CONTENT_WIDTH], hAlign="LEFT")
    holder.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("BOX", (0, 0), (-1, -1), 0.25, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return holder


# ---------------------------------------------------------------------------- parser

def parse(markdown, styles):
    """Translate the markdown subset used by project_report.md into flowables."""
    story = []
    lines = markdown.split("\n")
    index = 0
    seen_title = False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        # fenced code
        if stripped.startswith("```"):
            index += 1
            block = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            index += 1
            story.append(make_code(block, styles))
            continue

        # tables
        if stripped.startswith("|") and index + 1 < len(lines) and is_divider(lines[index + 1]):
            rows = [split_table_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_table_row(lines[index]))
                index += 1
            story.append(Spacer(1, 3))
            story.append(make_table(rows, styles))
            story.append(Spacer(1, 9))
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}", stripped):
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=RULE,
                                    spaceBefore=2, spaceAfter=8))
            index += 1
            continue

        # headings
        match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            if level == 1 and not seen_title:
                # The document title is rendered on the cover page instead.
                seen_title = True
                index += 1
                continue
            if level == 1:
                story.append(PageBreak())
                para = Paragraph(inline(text), styles["h1"])
                para.toc_level, para.toc_text = 0, text
                story.append(para)
                story.append(HRFlowable(width="100%", thickness=1.1, color=ACCENT,
                                        spaceBefore=3, spaceAfter=10))
            elif level == 2:
                para = Paragraph(inline(text), styles["h2"])
                para.toc_level, para.toc_text = 1, text
                story.append(para)
            elif level == 3:
                story.append(Paragraph(inline(text), styles["h3"]))
            else:
                story.append(Paragraph(inline(text), styles["h4"]))
            index += 1
            continue

        # unordered list
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^[-*]\s+", lines[index].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[index].strip()))
                index += 1
            for item in items:
                story.append(Paragraph(inline(item), styles["bullet"], bulletText="\u2022"))
            story.append(Spacer(1, 4))
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while index < len(lines) and re.match(r"^\d+\.\s+", lines[index].strip()):
                raw = lines[index].strip()
                number = raw.split(".", 1)[0]
                items.append((number, re.sub(r"^\d+\.\s+", "", raw)))
                index += 1
            for number, item in items:
                story.append(Paragraph(inline(item), styles["bullet"], bulletText=f"{number}."))
            story.append(Spacer(1, 4))
            continue

        # paragraph: gather until a blank line or a block starter
        block = []
        while index < len(lines):
            current = lines[index].strip()
            if not current:
                break
            if (current.startswith(("#", "|", "```", "- ", "* "))
                    or re.fullmatch(r"-{3,}", current)
                    or re.match(r"^\d+\.\s+", current)):
                break
            block.append(current)
            index += 1
        if block:
            story.append(Paragraph(inline(" ".join(block)), styles["body"]))

    return story


# ------------------------------------------------------------------- document layout

class ReportDoc(BaseDocTemplate):
    """Adds TOC notification and a page footer."""

    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)
        frame = Frame(MARGIN, MARGIN + 16, CONTENT_WIDTH,
                      PAGE_HEIGHT - 2 * MARGIN - 16, id="body")
        # One template only. A second template would never be reached without an
        # explicit NextPageTemplate, which is how the footer silently went missing.
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self.decorate)])

    def decorate(self, canvas, doc):
        if doc.page == 1:  # cover carries no furniture
            return
        canvas.saveState()
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, MARGIN + 6, PAGE_WIDTH - MARGIN, MARGIN + 6)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, MARGIN - 5, "AppSec Orchestrator — Project Briefing")
        canvas.drawRightString(PAGE_WIDTH - MARGIN, MARGIN - 5, f"Page {doc.page - 1}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        level = getattr(flowable, "toc_level", None)
        if level is not None:
            self.notify("TOCEntry", (level, flowable.toc_text, self.page - 1))


def cover(styles):
    return [
        Spacer(1, 1.5 * inch),
        Paragraph("AppSec Orchestrator", styles["title"]),
        Paragraph(
            "Project Briefing &mdash; architecture, features, current state, "
            "and VM deployment readiness",
            styles["subtitle"],
        ),
        Spacer(1, 0.35 * inch),
        HRFlowable(width="42%", thickness=2, color=ACCENT, hAlign="LEFT"),
        Spacer(1, 0.35 * inch),
        Paragraph(
            "A unified two-engine security platform: a source-code vulnerability scanner "
            "with an AI/pattern auto-fixer, merged with DeepSec, a document malware scanner. "
            "Both engines share one Scan &rarr; Finding &rarr; Report pipeline.",
            styles["body"],
        ),
        Spacer(1, 0.5 * inch),
        Paragraph("Generated 29 July 2026", styles["meta"]),
        Paragraph("Branch <b>main</b> &middot; commit <b>a77cf36</b>", styles["meta"]),
        Paragraph(
            "Every claim in this document was verified against source. "
            "Where the repository's own documentation disagrees with the code, "
            "this document follows the code &mdash; see section 3.2.",
            styles["meta"],
        ),
    ]


def main():
    if not SOURCE.exists():
        print(f"ERROR: source not found: {SOURCE}", file=sys.stderr)
        return 1

    styles = build_styles()
    markdown = SOURCE.read_text(encoding="utf-8")

    toc = TableOfContents()
    toc.levelStyles = [styles["toc1"], styles["toc2"]]
    # No dot leaders: they extract as long runs of stray periods, which is noise for
    # anything reading the PDF's text rather than looking at it.
    toc.dotsMinLevel = 99

    story = cover(styles)
    story.append(PageBreak())
    story.append(Paragraph("Contents", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=8))
    story.append(toc)
    story.extend(parse(markdown, styles))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = ReportDoc(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 16,
        title="AppSec Orchestrator — Project Briefing",
        author="AppSec Orchestrator",
        subject="Architecture, features, current state, and VM deployment readiness",
    )
    # multiBuild resolves TOC page numbers across passes.
    doc.multiBuild(story)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"Wrote {OUTPUT}  ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
