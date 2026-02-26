import sys
import os
import pytest
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
