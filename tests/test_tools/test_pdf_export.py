"""Tests for PDF export functionality."""

from pathlib import Path

import pytest

from synthera.tools.pdf_export import export_to_pdf, _parse_report_sections


class TestParseReportSections:
    def test_parses_markdown_headers(self):
        report = """
## Executive Summary
This is the summary.

## Key Findings
Finding 1 and Finding 2.

## Conclusion
Final thoughts here.
"""
        sections = _parse_report_sections(report)
        assert len(sections) >= 2
        headings = [s[0] for s in sections]
        assert any("Executive Summary" in h for h in headings)

    def test_handles_no_headers(self):
        report = "Just plain text without any headers."
        sections = _parse_report_sections(report)
        assert len(sections) >= 1


class TestPDFExport:
    def test_export_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("synthera.tools.pdf_export.REPORTS_DIR", tmp_path)

        citations = [
            {"title": "Source 1", "url": "https://example.com/1", "snippet": "Test snippet"},
            {"title": "Source 2", "url": "https://example.com/2", "snippet": "Another snippet"},
        ]

        report = """# Research Report

## Executive Summary
This is a test report about quantum computing advances.

## Key Findings
- Finding 1: Quantum supremacy demonstrated
- Finding 2: Error correction improved

## Conclusion
Quantum computing is progressing rapidly.
"""

        result_path = export_to_pdf(
            report=report,
            citations=citations,
            query="quantum computing advances",
        )

        assert result_path.exists()
        assert result_path.suffix == ".pdf"
        assert result_path.stat().st_size > 0

    def test_export_handles_empty_citations(self, tmp_path, monkeypatch):
        monkeypatch.setattr("synthera.tools.pdf_export.REPORTS_DIR", tmp_path)

        result_path = export_to_pdf(
            report="Simple report content",
            citations=[],
            query="test query",
        )

        assert result_path.exists()
