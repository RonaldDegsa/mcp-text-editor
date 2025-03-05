"""Tests for the MCP Text Editor Server."""

import json
from pathlib import Path
from typing import List

import pytest
from mcp.server import stdio
from mcp.types import ResourceTemplate, TextContent, Tool
from pytest_mock import MockerFixture

from mcp_text_editor.server import (
    GetTextFileContentsHandler,
    app,
    append_file_handler,
    call_tool,
    create_file_handler,
    delete_contents_handler,
    get_contents_handler,
    insert_file_handler,
    list_tools,
    list_resource_templates,
    main,
    patch_file_handler,
    read_resource,
)


@pytest.mark.asyncio
async def test_list_tools():
    """Test tool listing with enhanced descriptions and LLM guidance."""
    tools: List[Tool] = await list_tools()
    assert len(tools) == 6

    # Verify each tool has required components
    for tool in tools:
        assert tool.description is not None and len(tool.description) > 0
        assert tool.input_schema is not None
        assert "When " in tool.description.lower()

    # Verify GetTextFileContents tool specifically
    get_contents_tool = next(
        (tool for tool in tools if tool.name == "get_text_file_contents"), None
    )
    assert get_contents_tool is not None
    assert "line-range" in get_contents_tool.description.lower()
    assert "token usage" in get_contents_tool.description.lower()


@pytest.mark.asyncio
async def test_list_resource_templates():
    """Test resource template listing."""
    templates: List[ResourceTemplate] = await list_resource_templates()
    assert len(templates) == 1

    template = templates[0]
    assert template.uri_template == "text://{file_path}?lines={line_start}-{line_end}"
    assert template.name == "Line range access"
    assert template.mime_type == "text/plain"
    assert "Parameters:" in template.description
    assert "file_path:" in template.description
    assert "line_start:" in template.description
    assert "line_end:" in template.description


@pytest.mark.asyncio
async def test_read_resource_valid_uri(test_file):
    """Test read_resource with valid line range URI."""
    uri = f"text://{test_file}?lines=1-3"
    result = await read_resource(uri)
    assert isinstance(result, TextContent)
    assert result.type == "text"
    assert len(result.text) > 0


@pytest.mark.asyncio
async def test_read_resource_invalid_uri():
    """Test read_resource with invalid URI format."""
    invalid_uri = "invalid://path/to/file.txt"
    with pytest.raises(ValueError) as exc_info:
        await read_resource(invalid_uri)
    assert "Invalid URI scheme" in str(exc_info.value)


@pytest.mark.asyncio
async def test_read_resource_missing_parameters():
    """Test read_resource with missing required parameters."""
    uri = "text:///path/to/file.txt"  # Missing lines parameter
    with pytest.raises(ValueError) as exc_info:
        await read_resource(uri)
    assert "Missing 'lines' parameter" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_contents_empty_files():
    """Test get_contents handler with empty files list."""
    arguments = {"files": []}
    result = await get_contents_handler.run_tool(arguments)
    assert len(result) == 1
    assert result[0].type == "text"
    # Should return empty JSON object
    assert json.loads(result[0].text) == {}


@pytest.mark.asyncio
async def test_unknown_tool_handler():
    """Test handling of unknown tool name."""
    with pytest.raises(ValueError) as excinfo:
        await call_tool("unknown_tool", {})
    assert "Unknown tool: unknown_tool" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_contents_handler(test_file):
    """Test GetTextFileContents handler."""
    args = {"files": [{"file_path": test_file, "ranges": [{"line_start": 1, "line_end": 3}]}]}
    result = await get_contents_handler.run_tool(args)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    content = json.loads(result[0].text)
    assert test_file in content
    range_result = content[test_file]["ranges"][0]
    assert "content" in range_result
    assert "line_start" in range_result
    assert "line_end" in range_result
    assert "file_hash" in content[test_file]
    assert "total_lines" in range_result
    assert "content_size" in range_result


@pytest.mark.asyncio
async def test_get_contents_handler_invalid_file(test_file):
    """Test GetTextFileContents handler with invalid file."""
    # Convert relative path to absolute
    nonexistent_path = str(Path("nonexistent.txt").absolute())
    args = {"files": [{"file_path": nonexistent_path, "ranges": [{"line_start": 1}]}]}
    with pytest.raises(RuntimeError) as exc_info:
        await get_contents_handler.run_tool(args)
    assert "File not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_tool_get_contents(test_file):
    """Test call_tool with GetTextFileContents."""
    args = {"files": [{"file_path": test_file, "ranges": [{"line_start": 1, "line_end": 3}]}]}
    result = await call_tool("get_text_file_contents", args)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    content = json.loads(result[0].text)
    assert test_file in content
    range_result = content[test_file]["ranges"][0]
    assert "content" in range_result
    assert "line_start" in range_result
    assert "line_end" in range_result
    assert "file_hash" in content[test_file]
    assert "total_lines" in range_result
    assert "content_size" in range_result


@pytest.mark.asyncio
async def test_call_tool_unknown():
    """Test call_tool with unknown tool."""
    with pytest.raises(ValueError) as exc_info:
        await call_tool("UnknownTool", {})
    assert "Unknown tool" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_tool_error_handling():
    """Test call_tool error handling."""
    # Test with invalid arguments
    with pytest.raises(RuntimeError) as exc_info:
        await call_tool("get_text_file_contents", {"invalid": "args"})
    assert "Missing required argument" in str(exc_info.value)

    # Convert relative path to absolute
    nonexistent_path = str(Path("nonexistent.txt").absolute())
    with pytest.raises(RuntimeError) as exc_info:
        await call_tool(
            "get_text_file_contents",
            {"files": [{"file_path": nonexistent_path, "ranges": [{"line_start": 1}]}]},
        )
    assert "File not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_contents_handler_legacy_missing_args():
    """Test GetTextFileContents handler with legacy single file request missing arguments."""
    with pytest.raises(RuntimeError) as exc_info:
        await get_contents_handler.run_tool({})
    assert "Missing required argument: 'files'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_main_stdio_server_error(mocker: MockerFixture):
    """Test main function with stdio_server error."""
    # Mock the stdio_server to raise an exception
    mock_stdio = mocker.patch.object(stdio, "stdio_server")
    mock_stdio.side_effect = Exception("Stdio server error")

    with pytest.raises(Exception) as exc_info:
        await main()
    assert "Stdio server error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_main_run_error(mocker: MockerFixture):
    """Test main function with app.run error."""
    # Mock the stdio_server context manager
    mock_stdio = mocker.patch.object(stdio, "stdio_server")
    mock_context = mocker.MagicMock()
    mock_context.__aenter__.return_value = (mocker.MagicMock(), mocker.MagicMock())
    mock_stdio.return_value = mock_context

    # Mock app.run to raise an exception
    mock_run = mocker.patch.object(app, "run")
    mock_run.side_effect = Exception("App run error")

    with pytest.raises(Exception) as exc_info:
        await main()
    assert "App run error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_contents_relative_path():
    """Test GetTextFileContents with relative path."""
    handler = GetTextFileContentsHandler()
    with pytest.raises(RuntimeError, match="File path must be absolute:.*"):
        await handler.run_tool(
            {
                "files": [
                    {"file_path": "relative/path/file.txt", "ranges": [{"line_start": 1}]}
                ]
            }
        )


@pytest.mark.asyncio
async def test_get_contents_absolute_path():
    """Test GetTextFileContents with absolute path."""
    handler = GetTextFileContentsHandler()
    abs_path = str(Path("/absolute/path/file.txt").absolute())

    # Define mock as async function
    async def mock_read_multiple_ranges(*args, **kwargs):
        return []

    # Set up mock
    handler.editor.read_multiple_ranges = mock_read_multiple_ranges

    result = await handler.run_tool(
        {"files": [{"file_path": abs_path, "ranges": [{"line_start": 1}]}]}
    )
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_call_tool_general_exception():
    """Test call_tool with a general exception."""
    # Patch get_contents_handler.run_tool to raise a general exception
    original_run_tool = get_contents_handler.run_tool

    async def mock_run_tool(args):
        raise Exception("Unexpected error")

    try:
        get_contents_handler.run_tool = mock_run_tool
        with pytest.raises(RuntimeError) as exc_info:
            await call_tool("get_text_file_contents", {"files": []})
        assert "Error executing command: Unexpected error" in str(exc_info.value)
    finally:
        # Restore original method
        get_contents_handler.run_tool = original_run_tool


@pytest.mark.asyncio
async def test_call_tool_all_handlers(mocker: MockerFixture):
    """Test call_tool with all handlers."""
    # Mock run_tool for each handler
    handlers = [
        create_file_handler,
        append_file_handler,
        delete_contents_handler,
        insert_file_handler,
        patch_file_handler,
    ]

    # Setup mocks for all handlers
    async def mock_run_tool(args):
        return [TextContent(text="mocked response", type="text")]

    for handler in handlers:
        mock = mocker.patch.object(handler, "run_tool")
        mock.side_effect = mock_run_tool

    # Test each handler
    for handler in handlers:
        result = await call_tool(handler.name, {"test": "args"})
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "mocked response"
