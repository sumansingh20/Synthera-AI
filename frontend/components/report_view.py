"""Report view component — displays research results with citations and export."""

from __future__ import annotations

import httpx
import streamlit as st

API_BASE = "http://localhost:8000/api/v1"


def render_report(result: dict) -> None:
    """Render the complete research report with interactive elements.

    Args:
        result: Full research result dict from the API.
    """
    st.markdown("---")

    # ── Metrics Row ──────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sources Analyzed", result.get("documents_analyzed", 0))
    with col2:
        st.metric("Research Hops", result.get("hops_completed", 0))
    with col3:
        st.metric("Citations", len(result.get("citations", [])))
    with col4:
        st.metric("Status", result.get("status", "unknown").title())

    st.markdown("---")

    # ── Report Content ───────────────────────────────────
    report_text = result.get("report", "No report generated.")

    tab_report, tab_citations, tab_followup = st.tabs([
        "Report", "Citations", "Follow-up Questions"
    ])

    with tab_report:
        st.markdown(report_text)

    with tab_citations:
        citations = result.get("citations", [])
        if citations:
            for i, cite in enumerate(citations, 1):
                with st.container():
                    st.markdown(
                        f"**[{i}]** [{cite.get('title', 'Untitled')}]({cite.get('url', '#')})"
                    )
                    if cite.get("snippet"):
                        st.caption(cite["snippet"][:200])
                    st.markdown("---")
        else:
            st.info("No citations available.")

    with tab_followup:
        questions = result.get("follow_up_questions", [])
        if questions:
            st.markdown("Suggested follow-up research questions:")
            for q in questions:
                st.markdown(f"- {q}")
        else:
            st.info("No follow-up questions generated.")

    # ── Export Section ────────────────────────────────────
    st.markdown("---")
    st.markdown("### Export")

    col_export1, col_export2 = st.columns(2)

    with col_export1:
        if st.button("Export as PDF", use_container_width=True):
            task_id = result.get("task_id", "")
            if task_id:
                try:
                    resp = httpx.post(
                        f"{API_BASE}/research/export-pdf",
                        json={"task_id": task_id},
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        pdf_data = resp.json()
                        st.success(
                            f"PDF exported: {pdf_data['pdf_path']} "
                            f"({pdf_data['file_size_kb']:.1f} KB)"
                        )
                    else:
                        st.error("PDF export failed.")
                except Exception as e:
                    st.error(f"Export error: {e}")

    with col_export2:
        # Copy report text to clipboard via download button
        st.download_button(
            "Download Report (Markdown)",
            data=report_text,
            file_name="research_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # ── Errors ───────────────────────────────────────────
    errors = result.get("errors", [])
    if errors:
        with st.expander("Warnings & Errors"):
            for err in errors:
                st.warning(err)
