"""Streamlit application entry point for Synthera.

Provides a clean, interactive UI for submitting research queries,
monitoring progress, and viewing/exporting results.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.chat import render_research_input
from frontend.components.report_view import render_report

# ── Page Configuration ───────────────────────────────────
st.set_page_config(
    page_title="Synthera",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Custom CSS ──────────────────────────────────────
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────
if "research_history" not in st.session_state:
    st.session_state["research_history"] = []
if "current_result" not in st.session_state:
    st.session_state["current_result"] = None


def main() -> None:
    """Main application entry point."""

    # Header
    st.markdown("# Synthera")
    st.markdown(
        "Multi-Agent Research & Intelligence Platform — searches the web, "
        "reads articles, and synthesizes comprehensive reports with citations."
    )
    st.markdown("---")

    # Sidebar configuration
    config = render_sidebar()

    # Research input
    result = render_research_input(config)

    if result:
        st.session_state["current_result"] = result
        st.session_state["research_history"].append({
            "query": result.get("query", ""),
            "task_id": result.get("task_id", ""),
        })

    # Display current result
    if st.session_state["current_result"]:
        render_report(st.session_state["current_result"])

    # ── Research History ─────────────────────────────────
    if st.session_state["research_history"]:
        st.markdown("---")
        with st.expander("Research History"):
            for i, entry in enumerate(reversed(st.session_state["research_history"]), 1):
                st.markdown(f"**{i}.** {entry['query']}")
                st.caption(f"Task ID: `{entry['task_id']}`")


if __name__ == "__main__":
    main()
