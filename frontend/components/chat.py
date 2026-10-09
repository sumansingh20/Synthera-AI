"""Research input component — query input with streaming status updates."""

from __future__ import annotations

import time

import httpx
import streamlit as st

API_BASE = "http://localhost:8000/api/v1"


def _poll_research_status(task_id: str, status_container) -> dict | None:
    """Poll the API for research task status until completion."""
    while True:
        try:
            resp = httpx.get(f"{API_BASE}/research/status/{task_id}", timeout=10)
            if resp.status_code != 200:
                status_container.error("Failed to check status")
                return None

            data = resp.json()
            phase = data.get("phase", "unknown")
            progress = data.get("progress_pct", 0)
            docs = data.get("documents_collected", 0)

            status_container.markdown(
                f"**Phase:** {phase.title()} | "
                f"**Progress:** {progress}% | "
                f"**Documents:** {docs}"
            )

            if data["status"] in ("completed", "failed"):
                return data

            time.sleep(2)

        except Exception as e:
            status_container.error(f"Connection error: {e}")
            return None


def render_research_input(config: dict) -> dict | None:
    """Render the research query input and handle submission.

    Args:
        config: Research configuration from the sidebar.

    Returns:
        Research result dict if completed, None otherwise.
    """
    st.markdown("### What would you like to research?")

    query = st.text_area(
        "Enter your research question",
        placeholder="e.g., What are the latest advances in quantum computing and their potential commercial applications?",
        height=100,
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        start_btn = st.button("Start Research", type="primary", use_container_width=True)
    with col2:
        depth_badge = config["depth"].title()
        st.markdown(f"**Depth:** {depth_badge}")
    with col3:
        st.markdown(f"**Max Hops:** {config['max_hops']}")

    if start_btn and query.strip():
        st.markdown("---")
        status_container = st.empty()
        status_container.info("Submitting research request...")

        try:
            resp = httpx.post(
                f"{API_BASE}/research/start",
                json={
                    "query": query.strip(),
                    "depth": config["depth"],
                    "max_hops": config["max_hops"],
                },
                timeout=30,
            )

            if resp.status_code != 200:
                st.error(f"Failed to start research: {resp.text}")
                return None

            task_id = resp.json()["task_id"]
            st.session_state["current_task_id"] = task_id

            # Poll for completion
            result = _poll_research_status(task_id, status_container)

            if result and result["status"] == "completed":
                # Fetch full result
                full_resp = httpx.get(f"{API_BASE}/research/result/{task_id}", timeout=30)
                if full_resp.status_code == 200:
                    return full_resp.json()

            elif result and result["status"] == "failed":
                st.error("Research failed. Please try again with a different query.")

        except httpx.ConnectError:
            st.error(
                "Cannot connect to the API server. "
                "Make sure the backend is running: `make run-api`"
            )
        except Exception as e:
            st.error(f"Unexpected error: {e}")

    elif start_btn:
        st.warning("Please enter a research question.")

    return None
