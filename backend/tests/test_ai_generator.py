import sys
import os
from unittest.mock import MagicMock

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def _direct_response(mock_client, text="Direct answer"):
    """Set up mock client to return a simple end_turn response."""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [MagicMock(text=text)]
    mock_client.messages.create.return_value = mock_response
    return mock_response


def _tool_responses(
    mock_client,
    tool_name="search_course_content",
    tool_input=None,
    final_text="Final answer",
):
    """Set up mock client for a two-call tool-use flow. Returns the tool_block."""
    if tool_input is None:
        tool_input = {"query": "Python basics"}

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.id = "tool_abc123"
    tool_block.input = tool_input

    first_response = MagicMock()
    first_response.stop_reason = "tool_use"
    first_response.content = [tool_block]

    second_response = MagicMock()
    second_response.stop_reason = "end_turn"
    second_response.content = [MagicMock(text=final_text)]

    mock_client.messages.create.side_effect = [first_response, second_response]
    return tool_block


def _two_round_tool_responses(
    mock_client,
    tool_name="search_course_content",
    tool_input_1=None,
    tool_input_2=None,
    final_text="Final answer",
):
    """Set up mock client for a three-call two-round tool-use flow. Returns (tool_block_1, tool_block_2)."""
    if tool_input_1 is None:
        tool_input_1 = {"query": "round 1 query"}
    if tool_input_2 is None:
        tool_input_2 = {"query": "round 2 query"}

    tool_block_1 = MagicMock()
    tool_block_1.type = "tool_use"
    tool_block_1.name = tool_name
    tool_block_1.id = "tool_round1"
    tool_block_1.input = tool_input_1

    tool_block_2 = MagicMock()
    tool_block_2.type = "tool_use"
    tool_block_2.name = tool_name
    tool_block_2.id = "tool_round2"
    tool_block_2.input = tool_input_2

    first_response = MagicMock()
    first_response.stop_reason = "tool_use"
    first_response.content = [tool_block_1]

    second_response = MagicMock()
    second_response.stop_reason = "tool_use"
    second_response.content = [tool_block_2]

    third_response = MagicMock()
    third_response.stop_reason = "end_turn"
    third_response.content = [MagicMock(text=final_text)]

    mock_client.messages.create.side_effect = [
        first_response,
        second_response,
        third_response,
    ]
    return tool_block_1, tool_block_2


# ─── Direct response path ─────────────────────────────────────────────────────


def test_direct_response_returns_text(ai_generator, mock_anthropic_client):
    _direct_response(mock_anthropic_client, text="Direct answer")
    result = ai_generator.generate_response(query="What is Python?")
    assert result == "Direct answer"


def test_direct_response_makes_one_api_call(ai_generator, mock_anthropic_client):
    _direct_response(mock_anthropic_client)
    ai_generator.generate_response(query="What is Python?")
    assert mock_anthropic_client.messages.create.call_count == 1


def test_system_prompt_without_history(ai_generator, mock_anthropic_client):
    from ai_generator import AIGenerator

    _direct_response(mock_anthropic_client)
    ai_generator.generate_response(query="What is Python?")
    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    assert call_kwargs["system"] == AIGenerator.SYSTEM_PROMPT


def test_history_injected_into_system(ai_generator, mock_anthropic_client):
    from ai_generator import AIGenerator

    _direct_response(mock_anthropic_client)
    ai_generator.generate_response(
        query="What is Python?", conversation_history="User: hello"
    )
    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    assert "User: hello" in call_kwargs["system"]
    assert AIGenerator.SYSTEM_PROMPT in call_kwargs["system"]


def test_tools_and_tool_choice_present_when_tools_passed(
    ai_generator, mock_anthropic_client
):
    _direct_response(mock_anthropic_client)
    tools = [{"name": "search_course_content"}]
    ai_generator.generate_response(query="something", tools=tools)
    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    assert "tools" in call_kwargs
    assert call_kwargs["tools"] == tools
    assert "tool_choice" in call_kwargs


def test_no_tools_in_call_when_tools_is_none(ai_generator, mock_anthropic_client):
    _direct_response(mock_anthropic_client)
    ai_generator.generate_response(query="something", tools=None)
    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    assert "tools" not in call_kwargs
    assert "tool_choice" not in call_kwargs


# ─── Tool execution path ──────────────────────────────────────────────────────


def test_tool_manager_execute_called_correctly(ai_generator, mock_anthropic_client):
    tool_input = {"query": "Python basics", "course_name": "Intro"}
    _tool_responses(mock_anthropic_client, tool_input=tool_input)

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "search results"

    ai_generator.generate_response(
        query="What is Python?",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    mock_tool_manager.execute_tool.assert_called_once_with(
        "search_course_content",
        query="Python basics",
        course_name="Intro",
    )


def test_tool_path_makes_two_api_calls(ai_generator, mock_anthropic_client):
    _tool_responses(mock_anthropic_client)
    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )
    assert mock_anthropic_client.messages.create.call_count == 2


def test_second_call_has_tools(ai_generator, mock_anthropic_client):
    """Loop calls keep tools attached so Claude can make a second tool call if needed."""
    _tool_responses(mock_anthropic_client)
    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    tools = [{"name": "search_course_content"}]
    ai_generator.generate_response(
        query="something",
        tools=tools,
        tool_manager=mock_tool_manager,
    )

    second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1].kwargs
    assert "tools" in second_call_kwargs
    assert "tool_choice" in second_call_kwargs


def test_second_call_messages_structure(ai_generator, mock_anthropic_client):
    tool_input = {"query": "Python"}
    _tool_responses(mock_anthropic_client, tool_input=tool_input)

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "tool output"

    ai_generator.generate_response(
        query="What is Python?",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    second_call_kwargs = mock_anthropic_client.messages.create.call_args_list[1].kwargs
    messages = second_call_kwargs["messages"]

    # messages[0]: original user message
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is Python?"

    # messages[1]: assistant tool_use
    assert messages[1]["role"] == "assistant"

    # messages[2]: user with tool_result
    assert messages[2]["role"] == "user"
    tool_result = messages[2]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["content"] == "tool output"


def test_final_response_text_from_second_call(ai_generator, mock_anthropic_client):
    _tool_responses(mock_anthropic_client, final_text="The final answer")
    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    result = ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )
    assert result == "The final answer"


def test_no_tool_manager_falls_through_to_text(ai_generator, mock_anthropic_client):
    """When tool_manager=None and stop_reason=tool_use, returns content[0].text without a second call."""
    mock_text = MagicMock()
    mock_text.text = "fallback text"

    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"
    mock_response.content = [mock_text]
    mock_anthropic_client.messages.create.return_value = mock_response

    result = ai_generator.generate_response(query="something", tool_manager=None)
    assert result == "fallback text"
    assert mock_anthropic_client.messages.create.call_count == 1


# ─── Multi-round tool execution path ──────────────────────────────────────────


def test_two_round_tool_path_makes_three_api_calls(ai_generator, mock_anthropic_client):
    _two_round_tool_responses(mock_anthropic_client)
    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )
    assert mock_anthropic_client.messages.create.call_count == 3


def test_two_round_tool_manager_execute_called_twice(
    ai_generator, mock_anthropic_client
):
    tool_input_1 = {"query": "round 1"}
    tool_input_2 = {"query": "round 2"}
    _two_round_tool_responses(
        mock_anthropic_client, tool_input_1=tool_input_1, tool_input_2=tool_input_2
    )

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    assert mock_tool_manager.execute_tool.call_count == 2
    mock_tool_manager.execute_tool.assert_any_call(
        "search_course_content", query="round 1"
    )
    mock_tool_manager.execute_tool.assert_any_call(
        "search_course_content", query="round 2"
    )


def test_two_round_second_and_third_calls_have_tools(
    ai_generator, mock_anthropic_client
):
    """When cap is hit (3x tool_use), loop calls [1] and [2] have tools; only final call [3] omits them."""
    tool_block_1 = MagicMock()
    tool_block_1.type = "tool_use"
    tool_block_1.name = "search_course_content"
    tool_block_1.id = "id1"
    tool_block_1.input = {"query": "q1"}
    tool_block_2 = MagicMock()
    tool_block_2.type = "tool_use"
    tool_block_2.name = "search_course_content"
    tool_block_2.id = "id2"
    tool_block_2.input = {"query": "q2"}
    tool_block_3 = MagicMock()
    tool_block_3.type = "tool_use"
    tool_block_3.name = "search_course_content"
    tool_block_3.id = "id3"
    tool_block_3.input = {"query": "q3"}

    r1 = MagicMock()
    r1.stop_reason = "tool_use"
    r1.content = [tool_block_1]
    r2 = MagicMock()
    r2.stop_reason = "tool_use"
    r2.content = [tool_block_2]
    r3 = MagicMock()
    r3.stop_reason = "tool_use"
    r3.content = [tool_block_3]
    r4 = MagicMock()
    r4.stop_reason = "end_turn"
    r4.content = [MagicMock(text="final")]

    mock_anthropic_client.messages.create.side_effect = [r1, r2, r3, r4]

    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    call_args_list = mock_anthropic_client.messages.create.call_args_list
    assert mock_anthropic_client.messages.create.call_count == 4

    # Loop calls [1] and [2] include tools
    assert "tools" in call_args_list[1].kwargs
    assert "tool_choice" in call_args_list[1].kwargs
    assert "tools" in call_args_list[2].kwargs
    assert "tool_choice" in call_args_list[2].kwargs

    # Final forced call [3] omits tools
    assert "tools" not in call_args_list[3].kwargs
    assert "tool_choice" not in call_args_list[3].kwargs


def test_two_round_early_exit_makes_two_api_calls(ai_generator, mock_anthropic_client):
    """end_turn on the first loop iteration exits early — no extra final call."""
    _tool_responses(mock_anthropic_client, final_text="early exit answer")
    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    result = ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )

    assert mock_anthropic_client.messages.create.call_count == 2
    assert result == "early exit answer"


def test_two_round_final_response_text(ai_generator, mock_anthropic_client):
    _two_round_tool_responses(
        mock_anthropic_client, final_text="Two round final answer"
    )
    mock_tool_manager = MagicMock()
    mock_tool_manager.execute_tool.return_value = "results"

    result = ai_generator.generate_response(
        query="something",
        tools=[{"name": "search_course_content"}],
        tool_manager=mock_tool_manager,
    )
    assert result == "Two round final answer"
