"""Sidebar component — research configuration and settings panel."""

from __future__ import annotations

import streamlit as st


def render_sidebar() -> dict:
    """Render the sidebar with research configuration options.

    Returns:
        Dictionary with selected configuration values.
    """
    with st.sidebar:
        st.markdown("## Research Settings")
        st.markdown("---")

        # Depth selector
        depth = st.selectbox(
            "Research Depth",
            options=["quick", "moderate", "comprehensive"],
            index=2,
            help=(
                "**Quick**: Single search pass, top 3 results.\n"
                "**Moderate**: 2 hops, top 5 results per hop.\n"
                "**Comprehensive**: Up to max hops, full result set."
            ),
        )

        # Max hops slider
        max_hops = st.slider(
            "Max Research Hops",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of search → scrape → analyze cycles.",
        )

        st.markdown("---")

        # Advanced settings
        with st.expander("Advanced Settings"):
            max_results = st.number_input(
                "Max Search Results per Query",
                min_value=1,
                max_value=50,
                value=10,
            )

            concurrent_scrapes = st.number_input(
                "Concurrent Scrape Limit",
                min_value=1,
                max_value=20,
                value=5,
            )

            export_pdf = st.checkbox("Auto-export PDF on completion", value=False)

        st.markdown("---")

        # Status info
        st.markdown("### About")
        st.markdown(
            "Multi-agent research tool that searches the web, "
            "reads articles, and synthesizes comprehensive reports "
            "with citations."
        )
        st.markdown("---")
        st.caption("Powered by LangGraph + RAG + LangSmith")

    return {
        "depth": depth,
        "max_hops": max_hops,
        "max_results": max_results,
        "concurrent_scrapes": concurrent_scrapes,
        "export_pdf": export_pdf,
    }
