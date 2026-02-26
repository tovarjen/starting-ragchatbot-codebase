import sys
import os
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture
def patched_rag_system():
    mock_config = MagicMock()
    mock_config.CHUNK_SIZE = 800
    mock_config.CHUNK_OVERLAP = 100
    mock_config.CHROMA_PATH = "/fake/path"
    mock_config.EMBEDDING_MODEL = "fake-model"
    mock_config.MAX_RESULTS = 5
    mock_config.ANTHROPIC_API_KEY = "fake-key"
    mock_config.ANTHROPIC_MODEL = "fake-model"
    mock_config.MAX_HISTORY = 5

    with patch("rag_system.DocumentProcessor"), \
         patch("rag_system.VectorStore") as MockVectorStore, \
         patch("rag_system.AIGenerator") as MockAIGen, \
         patch("rag_system.SessionManager") as MockSession, \
         patch("rag_system.ToolManager") as MockToolMgr, \
         patch("rag_system.CourseSearchTool"), \
         patch("rag_system.CourseOutlineTool"):

        from rag_system import RAGSystem
        rag = RAGSystem(mock_config)

        # Expose mock instances for test assertions
        rag._mock_ai_generator = MockAIGen.return_value
        rag._mock_session_manager = MockSession.return_value
        rag._mock_tool_manager = MockToolMgr.return_value
        rag._mock_vector_store = MockVectorStore.return_value

        # Sensible defaults
        rag._mock_ai_generator.generate_response.return_value = "AI response"
        rag._mock_session_manager.get_conversation_history.return_value = "past history"
        rag._mock_tool_manager.get_tool_definitions.return_value = [
            {"name": "search_course_content"}
        ]
        rag._mock_tool_manager.get_last_sources.return_value = [
            {"text": "Python 101 - Lesson 1", "url": "http://ex.com"}
        ]

        yield rag


# ─── Return value shape ───────────────────────────────────────────────────────

def test_query_returns_tuple(patched_rag_system):
    result = patched_rag_system.query("What is Python?")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_response_text_from_ai_generator(patched_rag_system):
    response, _ = patched_rag_system.query("What is Python?")
    assert response == "AI response"


def test_sources_from_tool_manager(patched_rag_system):
    _, sources = patched_rag_system.query("What is Python?")
    assert sources == [{"text": "Python 101 - Lesson 1", "url": "http://ex.com"}]


# ─── Prompt construction ──────────────────────────────────────────────────────

def test_query_wrapped_in_prompt(patched_rag_system):
    patched_rag_system.query("What is a decorator?")
    call_kwargs = patched_rag_system._mock_ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["query"] == "Answer this question about course materials: What is a decorator?"


def test_raw_query_not_passed_unchanged(patched_rag_system):
    raw_query = "What is a decorator?"
    patched_rag_system.query(raw_query)
    call_kwargs = patched_rag_system._mock_ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["query"] != raw_query


# ─── Session handling ─────────────────────────────────────────────────────────

def test_get_history_called_with_session_id(patched_rag_system):
    patched_rag_system.query("question", session_id="sess-1")
    patched_rag_system._mock_session_manager.get_conversation_history.assert_called_once_with(
        "sess-1"
    )


def test_no_history_call_without_session_id(patched_rag_system):
    patched_rag_system.query("question", session_id=None)
    patched_rag_system._mock_session_manager.get_conversation_history.assert_not_called()


def test_add_exchange_called_with_session_id(patched_rag_system):
    patched_rag_system.query("What is Python?", session_id="sess-1")
    patched_rag_system._mock_session_manager.add_exchange.assert_called_once_with(
        "sess-1", "What is Python?", "AI response"
    )


def test_no_exchange_saved_without_session_id(patched_rag_system):
    patched_rag_system.query("What is Python?", session_id=None)
    patched_rag_system._mock_session_manager.add_exchange.assert_not_called()


# ─── Tool manager wiring ──────────────────────────────────────────────────────

def test_tool_definitions_forwarded_to_generate_response(patched_rag_system):
    patched_rag_system.query("question")
    call_kwargs = patched_rag_system._mock_ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["tools"] == [{"name": "search_course_content"}]


def test_tool_manager_passed_to_generate_response(patched_rag_system):
    patched_rag_system.query("question")
    call_kwargs = patched_rag_system._mock_ai_generator.generate_response.call_args.kwargs
    assert call_kwargs["tool_manager"] is patched_rag_system._mock_tool_manager


def test_reset_sources_called_after_get_last_sources(patched_rag_system):
    patched_rag_system.query("question")
    patched_rag_system._mock_tool_manager.get_last_sources.assert_called_once()
    patched_rag_system._mock_tool_manager.reset_sources.assert_called_once()


# ─── Content-query integration scenario ──────────────────────────────────────

def test_full_pipeline_with_session(patched_rag_system):
    response, sources = patched_rag_system.query("Explain classes", session_id="s1")

    # History was fetched
    patched_rag_system._mock_session_manager.get_conversation_history.assert_called_once_with("s1")

    # AI was called with the wrapped prompt and the fetched history
    call_kwargs = patched_rag_system._mock_ai_generator.generate_response.call_args.kwargs
    assert "Explain classes" in call_kwargs["query"]
    assert call_kwargs["conversation_history"] == "past history"

    # Exchange saved with the raw query
    patched_rag_system._mock_session_manager.add_exchange.assert_called_once_with(
        "s1", "Explain classes", response
    )

    # Sources returned
    assert len(sources) == 1


def test_empty_sources_when_no_tool_used(patched_rag_system):
    patched_rag_system._mock_tool_manager.get_last_sources.return_value = []
    _, sources = patched_rag_system.query("question")
    assert sources == []
