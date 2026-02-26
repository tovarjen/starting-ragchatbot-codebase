import sys
import os
import pytest
from typing import List, Optional
from unittest.mock import MagicMock, patch

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from vector_store import SearchResults


@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.get_lesson_link.return_value = None
    store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    return store


@pytest.fixture
def course_search_tool(mock_vector_store):
    from search_tools import CourseSearchTool

    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def mock_anthropic_client():
    with patch("anthropic.Anthropic") as MockClass:
        mock_instance = MagicMock()
        MockClass.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def ai_generator(mock_anthropic_client):
    from ai_generator import AIGenerator

    return AIGenerator(api_key="fake-key", model="claude-test-model")


# ─── API endpoint fixtures ────────────────────────────────────────────────────

@pytest.fixture
def mock_rag_system():
    """Mock RAGSystem with sensible defaults for API endpoint tests."""
    mock = MagicMock()
    mock.query.return_value = (
        "Test answer",
        [{"text": "Python 101 - Lesson 1", "url": "http://example.com"}],
    )
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Python 101", "AI Fundamentals"],
    }
    mock.session_manager.create_session.return_value = "new-session-id"
    return mock


@pytest.fixture
def test_client(mock_rag_system):
    """TestClient backed by a minimal FastAPI app wired to mock_rag_system.

    Defines the three API routes inline to avoid the static-file mount in
    app.py that fails when the frontend directory doesn't exist in CI/tests.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from pydantic import BaseModel

    _app = FastAPI()

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[dict]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    @_app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @_app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @_app.delete("/api/session/{session_id}")
    async def delete_session(session_id: str):
        mock_rag_system.session_manager.clear_session(session_id)
        return {"status": "cleared"}

    with TestClient(_app) as client:
        yield client
