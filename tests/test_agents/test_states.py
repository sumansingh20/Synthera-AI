"""Tests for research state management."""

from synthera.agents.states import ResearchState, ResearchPhase, ResearchDepth


class TestResearchState:
    def test_default_state_has_required_keys(self):
        state = ResearchState.default()
        assert "query" in state
        assert "depth" in state
        assert "phase" in state
        assert "documents" in state
        assert "search_results" in state
        assert "report" in state
        assert "citations" in state

    def test_default_state_initial_values(self):
        state = ResearchState.default()
        assert state["query"] == ""
        assert state["phase"] == ResearchPhase.PLANNING.value
        assert state["current_hop"] == 0
        assert state["documents"] == []
        assert state["errors"] == []

    def test_default_depth_is_comprehensive(self):
        state = ResearchState.default()
        assert state["depth"] == ResearchDepth.COMPREHENSIVE.value


class TestResearchPhase:
    def test_all_phases_exist(self):
        phases = [p.value for p in ResearchPhase]
        assert "planning" in phases
        assert "searching" in phases
        assert "scraping" in phases
        assert "analyzing" in phases
        assert "synthesizing" in phases
        assert "complete" in phases
        assert "error" in phases


class TestResearchDepth:
    def test_depth_values(self):
        assert ResearchDepth.QUICK.value == "quick"
        assert ResearchDepth.MODERATE.value == "moderate"
        assert ResearchDepth.COMPREHENSIVE.value == "comprehensive"
