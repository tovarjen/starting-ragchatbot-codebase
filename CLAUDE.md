# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Always use `uv` to manage dependencies and run Python commands — never use `pip` directly.

All commands must be run from the `backend/` directory using `uv run`:

```bash
# Start the server (from project root)
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000
```

App is served at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

**Dependencies** (from project root):
```bash
uv sync                    # install/sync dependencies
uv run python script.py    # run any Python file
```

**Environment** — create a `.env` in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

There are no tests in this codebase.

## Architecture

This is a RAG (Retrieval-Augmented Generation) system with a FastAPI backend and plain HTML/JS frontend.

### RAG Pipeline

`RAGSystem` (`rag_system.py`) is the central orchestrator. A query goes through three stages:

1. **Retrieve history** — `SessionManager` returns the last N conversation turns as a plain string, injected into the Claude *system prompt* (not the messages array).
2. **Two-call Claude loop** — `AIGenerator` makes a first call with the `search_course_content` tool attached. If Claude triggers the tool, `_handle_tool_execution` runs the search, appends tool results to the messages list, and makes a second call (without tools) to get the final answer.
3. **Vector search** — `CourseSearchTool` delegates to `VectorStore.search()`, which optionally resolves a fuzzy course name via semantic search on the `course_catalog` collection, then queries `course_content` with an optional ChromaDB `where` filter.

### Two ChromaDB Collections

- `course_catalog` — one document per course (title, instructor, links, lessons as serialized JSON). Used for fuzzy course-name resolution.
- `course_content` — one document per text chunk (800 chars, 100-char sentence-boundary overlap). Filtered by `course_title` and/or `lesson_number` at query time.

### Document Format

Course `.txt` files in `docs/` must follow this structure for `DocumentProcessor` to parse them correctly:

```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 1: <title>
Lesson Link: <url>
<lesson text...>

Lesson 2: <title>
...
```

`DocumentProcessor.process_course_document()` extracts the metadata from the first 3 lines, then splits remaining content on `Lesson N:` markers. On server startup, `add_course_folder()` skips already-indexed courses (deduplication by title).

### Tool Interface

`search_tools.py` defines a `Tool` ABC. New tools can be registered with `ToolManager.register_tool()` and will automatically be included in Claude API calls — no changes needed to `AIGenerator`. `CourseSearchTool` stores `last_sources` as instance state after each search; this is not concurrency-safe.

### Config

All tunable settings live in `backend/config.py`: model name, embedding model (`all-MiniLM-L6-v2`), chunk size/overlap, max search results, and max history turns.
