"""PDF export tool — generates formatted PDF reports from research output.

Uses fpdf2 to create clean, professional PDF documents with
proper typography, headers, citations, and page numbering.
"""

from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime, timezone

from fpdf import FPDF

from synthera.utils import get_logger, sanitize_filename

logger = get_logger(__name__)

REPORTS_DIR = Path("reports_output")


class ResearchPDF(FPDF):
    """Custom PDF class with headers, footers, and research-specific formatting."""

    def __init__(self, title: str = "Research Report"):
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=25)

    def header(self) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, self.report_title, align="L")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title_page(self, title: str, metadata: dict) -> None:
        """Add a formatted title page with research metadata."""
        self.add_page()
        self.ln(40)

        # Title
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 12, title, align="C")
        self.ln(15)

        # Divider
        self.set_draw_color(70, 130, 180)
        self.set_line_width(0.8)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(15)

        # Metadata
        self.set_font("Helvetica", "", 11)
        self.set_text_color(80, 80, 80)
        for key, value in metadata.items():
            self.cell(0, 8, f"{key}: {value}", align="C")
            self.ln(7)

    def add_section(self, heading: str, body: str) -> None:
        """Add a section with heading and body text."""
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 60, 120)
        self.ln(5)
        self.multi_cell(0, 8, heading)
        self.ln(3)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, body)
        self.ln(4)

    def add_citations(self, citations: list[dict]) -> None:
        """Add a formatted references/citations section."""
        self.add_page()
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 60, 120)
        self.cell(0, 10, "References", align="L")
        self.ln(12)

        for i, cite in enumerate(citations, 1):
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(40, 40, 40)
            self.cell(0, 6, f"[{i}] {cite.get('title', 'Untitled')}")
            self.ln(5)

            self.set_font("Helvetica", "", 8)
            self.set_text_color(70, 130, 180)
            self.cell(0, 5, cite.get("url", ""))
            self.ln(5)

            if cite.get("snippet"):
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(100, 100, 100)
                self.multi_cell(0, 5, cite["snippet"][:200])

            self.ln(4)


def _parse_report_sections(report_text: str) -> list[tuple[str, str]]:
    """Split a markdown-style report into (heading, body) sections."""
    sections = []
    # Split on markdown headers (## or #)
    parts = re.split(r"\n(#{1,3}\s+.+)\n", report_text)

    current_heading = "Overview"
    current_body = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.match(r"^#{1,3}\s+", part):
            if current_body.strip():
                sections.append((current_heading, current_body.strip()))
            current_heading = re.sub(r"^#{1,3}\s+", "", part)
            current_body = ""
        else:
            current_body += part + "\n"

    if current_body.strip():
        sections.append((current_heading, current_body.strip()))

    return sections


def export_to_pdf(
    report: str,
    citations: list[dict],
    query: str,
    metadata: dict | None = None,
) -> Path:
    """Export a research report to a formatted PDF file.

    Args:
        report: Full report text (markdown format).
        citations: List of citation dicts with title, url, snippet.
        query: Original research query.
        metadata: Optional metadata dict for the title page.

    Returns:
        Path to the generated PDF file.
    """
    REPORTS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{sanitize_filename(query)}_{timestamp}.pdf"
    output_path = REPORTS_DIR / filename

    pdf = ResearchPDF(title=query[:60])
    pdf.alias_nb_pages()

    # Title page
    title_metadata = metadata or {
        "Research Query": query,
        "Generated": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "Sources": str(len(citations)),
    }
    pdf.add_title_page(f"Research Report:\n{query}", title_metadata)

    # Content sections
    sections = _parse_report_sections(report)
    pdf.add_page()
    for heading, body in sections:
        # Clean markdown artifacts for PDF
        clean_body = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
        clean_body = re.sub(r"\*(.+?)\*", r"\1", clean_body)
        clean_body = re.sub(r"`(.+?)`", r"\1", clean_body)
        pdf.add_section(heading, clean_body)

    # Citations
    if citations:
        pdf.add_citations(citations)

    pdf.output(str(output_path))
    logger.info("PDF exported: %s (%d pages)", output_path, pdf.page_no())

    return output_path
