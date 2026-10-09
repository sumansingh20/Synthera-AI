"""Tests for the FastAPI application endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from synthera.api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestRootEndpoint:
    @pytest.mark.asyncio
    async def test_root_returns_app_info(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Synthera"
        assert "version" in data
        assert "docs" in data


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    @pytest.mark.asyncio
    async def test_health_includes_services(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "api" in data["services"]
        assert "vectorstore" in data["services"]
        assert "llm_model" in data["services"]


class TestResearchEndpoints:
    @pytest.mark.asyncio
    async def test_start_research_validation(self, client):
        # Empty query should fail validation
        response = await client.post(
            "/api/v1/research/start",
            json={"query": "ab", "depth": "quick"},  # too short
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_status_not_found(self, client):
        response = await client.get("/api/v1/research/status/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_result_not_found(self, client):
        response = await client.get("/api/v1/research/result/nonexistent-id")
        assert response.status_code == 404
