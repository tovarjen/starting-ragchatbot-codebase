import pytest


# ─── POST /api/query ──────────────────────────────────────────────────────────

def test_query_returns_200(test_client):
    response = test_client.post("/api/query", json={"query": "What is Python?"})
    assert response.status_code == 200


def test_query_response_has_answer(test_client):
    response = test_client.post("/api/query", json={"query": "What is Python?"})
    assert response.json()["answer"] == "Test answer"


def test_query_response_has_sources(test_client):
    response = test_client.post("/api/query", json={"query": "What is Python?"})
    sources = response.json()["sources"]
    assert isinstance(sources, list)
    assert len(sources) == 1
    assert sources[0]["text"] == "Python 101 - Lesson 1"


def test_query_response_has_session_id(test_client):
    response = test_client.post("/api/query", json={"query": "What is Python?"})
    assert "session_id" in response.json()


def test_query_generates_session_when_none_provided(test_client, mock_rag_system):
    response = test_client.post("/api/query", json={"query": "What is Python?"})
    mock_rag_system.session_manager.create_session.assert_called_once()
    assert response.json()["session_id"] == "new-session-id"


def test_query_uses_provided_session_id(test_client, mock_rag_system):
    test_client.post("/api/query", json={"query": "something", "session_id": "my-session"})
    mock_rag_system.session_manager.create_session.assert_not_called()
    mock_rag_system.query.assert_called_once_with("something", "my-session")


def test_query_provided_session_id_echoed_in_response(test_client):
    response = test_client.post(
        "/api/query", json={"query": "something", "session_id": "my-session"}
    )
    assert response.json()["session_id"] == "my-session"


def test_query_missing_query_field_returns_422(test_client):
    response = test_client.post("/api/query", json={})
    assert response.status_code == 422


def test_query_rag_error_returns_500(test_client, mock_rag_system):
    mock_rag_system.query.side_effect = RuntimeError("DB connection failed")
    response = test_client.post(
        "/api/query", json={"query": "something", "session_id": "s1"}
    )
    assert response.status_code == 500
    assert "DB connection failed" in response.json()["detail"]


# ─── GET /api/courses ─────────────────────────────────────────────────────────

def test_courses_returns_200(test_client):
    response = test_client.get("/api/courses")
    assert response.status_code == 200


def test_courses_response_has_total_courses(test_client):
    response = test_client.get("/api/courses")
    assert response.json()["total_courses"] == 2


def test_courses_response_has_course_titles(test_client):
    response = test_client.get("/api/courses")
    assert response.json()["course_titles"] == ["Python 101", "AI Fundamentals"]


def test_courses_analytics_error_returns_500(test_client, mock_rag_system):
    mock_rag_system.get_course_analytics.side_effect = RuntimeError("Analytics failed")
    response = test_client.get("/api/courses")
    assert response.status_code == 500
    assert "Analytics failed" in response.json()["detail"]


# ─── DELETE /api/session/{session_id} ─────────────────────────────────────────

def test_delete_session_returns_200(test_client):
    response = test_client.delete("/api/session/abc123")
    assert response.status_code == 200


def test_delete_session_returns_cleared_status(test_client):
    response = test_client.delete("/api/session/abc123")
    assert response.json() == {"status": "cleared"}


def test_delete_session_calls_clear_with_correct_id(test_client, mock_rag_system):
    test_client.delete("/api/session/abc123")
    mock_rag_system.session_manager.clear_session.assert_called_once_with("abc123")
