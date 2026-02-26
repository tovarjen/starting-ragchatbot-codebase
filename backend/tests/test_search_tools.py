import sys
import os

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from vector_store import SearchResults

# ─── Error path ───────────────────────────────────────────────────────────────


def test_error_returned_from_search(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = SearchResults(
        documents=[], metadata=[], distances=[], error="DB connection failed"
    )
    result = course_search_tool.execute(query="Python basics")
    assert result == "DB connection failed"


def test_error_returned_before_empty_check(course_search_tool, mock_vector_store):
    """Error takes priority even when documents are present."""
    mock_vector_store.search.return_value = SearchResults(
        documents=["some content"],
        metadata=[{}],
        distances=[0.5],
        error="Partial failure",
    )
    result = course_search_tool.execute(query="Python basics")
    assert result == "Partial failure"


# ─── Empty results path ───────────────────────────────────────────────────────


def test_empty_no_filters(course_search_tool):
    result = course_search_tool.execute(query="Python basics")
    assert result == "No relevant content found."


def test_empty_with_course_name(course_search_tool):
    result = course_search_tool.execute(query="Python basics", course_name="MCP Course")
    assert "in course 'MCP Course'" in result


def test_empty_with_lesson_number(course_search_tool):
    result = course_search_tool.execute(query="Python basics", lesson_number=3)
    assert "in lesson 3" in result


def test_lesson_number_zero_missing_from_empty_message(course_search_tool):
    """lesson_number=0 must appear; currently fails because `if lesson_number:` treats 0 as falsy."""
    result = course_search_tool.execute(query="Python basics", lesson_number=0)
    assert "lesson 0" in result


def test_empty_with_both_filters(course_search_tool):
    result = course_search_tool.execute(
        query="Python basics", course_name="MCP", lesson_number=2
    )
    assert "in course 'MCP'" in result
    assert "in lesson 2" in result


# ─── Search argument forwarding ───────────────────────────────────────────────


def test_query_forwarded_to_store(course_search_tool, mock_vector_store):
    course_search_tool.execute(query="decorators in Python")
    assert mock_vector_store.search.call_args.kwargs["query"] == "decorators in Python"


def test_course_name_forwarded_to_store(course_search_tool, mock_vector_store):
    course_search_tool.execute(query="anything", course_name="Intro to AI")
    assert mock_vector_store.search.call_args.kwargs["course_name"] == "Intro to AI"


def test_lesson_number_forwarded_to_store(course_search_tool, mock_vector_store):
    course_search_tool.execute(query="anything", lesson_number=5)
    assert mock_vector_store.search.call_args.kwargs["lesson_number"] == 5


# ─── last_sources population ──────────────────────────────────────────────────


def test_last_sources_empty_before_call(course_search_tool):
    assert course_search_tool.last_sources == []


def test_last_sources_populated_after_search(course_search_tool, mock_vector_store):
    mock_vector_store.get_lesson_link.return_value = "http://example.com/lesson1"
    mock_vector_store.search.return_value = SearchResults(
        documents=["content here"],
        metadata=[{"course_title": "Python 101", "lesson_number": 1}],
        distances=[0.1],
    )
    course_search_tool.execute(query="Python basics")
    assert len(course_search_tool.last_sources) == 1
    assert course_search_tool.last_sources[0]["text"] == "Python 101 - Lesson 1"
    assert course_search_tool.last_sources[0]["url"] == "http://example.com/lesson1"


def test_multiple_results_produce_multiple_sources(
    course_search_tool, mock_vector_store
):
    mock_vector_store.search.return_value = SearchResults(
        documents=["doc1", "doc2"],
        metadata=[
            {"course_title": "Course A", "lesson_number": 1},
            {"course_title": "Course B", "lesson_number": 2},
        ],
        distances=[0.1, 0.2],
    )
    course_search_tool.execute(query="something")
    assert len(course_search_tool.last_sources) == 2


def test_no_lesson_number_in_metadata_gives_none_url(
    course_search_tool, mock_vector_store
):
    mock_vector_store.search.return_value = SearchResults(
        documents=["content"],
        metadata=[{"course_title": "Python 101"}],  # no lesson_number key
        distances=[0.1],
    )
    course_search_tool.execute(query="something")
    assert course_search_tool.last_sources[0]["url"] is None
    mock_vector_store.get_lesson_link.assert_not_called()


def test_subsequent_call_overwrites_sources(course_search_tool, mock_vector_store):
    # First call: one source
    mock_vector_store.search.return_value = SearchResults(
        documents=["doc1"],
        metadata=[{"course_title": "Course A", "lesson_number": 1}],
        distances=[0.1],
    )
    course_search_tool.execute(query="first query")
    assert len(course_search_tool.last_sources) == 1

    # Second call: two sources
    mock_vector_store.search.return_value = SearchResults(
        documents=["doc2", "doc3"],
        metadata=[
            {"course_title": "Course B", "lesson_number": 2},
            {"course_title": "Course C", "lesson_number": 3},
        ],
        distances=[0.2, 0.3],
    )
    course_search_tool.execute(query="second query")
    assert len(course_search_tool.last_sources) == 2


# ─── Output formatting ────────────────────────────────────────────────────────


def test_output_contains_header_and_content(course_search_tool, mock_vector_store):
    mock_vector_store.search.return_value = SearchResults(
        documents=["The content here"],
        metadata=[{"course_title": "Python 101", "lesson_number": 2}],
        distances=[0.1],
    )
    result = course_search_tool.execute(query="something")
    assert "[Python 101 - Lesson 2]" in result
    assert "The content here" in result


def test_multiple_results_separated_by_double_newline(
    course_search_tool, mock_vector_store
):
    mock_vector_store.search.return_value = SearchResults(
        documents=["First doc", "Second doc"],
        metadata=[
            {"course_title": "Course A", "lesson_number": 1},
            {"course_title": "Course B", "lesson_number": 2},
        ],
        distances=[0.1, 0.2],
    )
    result = course_search_tool.execute(query="something")
    parts = result.split("\n\n")
    assert len(parts) == 2


def test_no_lesson_in_header_without_lesson_number(
    course_search_tool, mock_vector_store
):
    mock_vector_store.search.return_value = SearchResults(
        documents=["content"],
        metadata=[{"course_title": "Python 101"}],  # no lesson_number
        distances=[0.1],
    )
    result = course_search_tool.execute(query="something")
    assert "[Python 101]" in result
    assert "Lesson" not in result
