"""Tests for the peek_text_file_contents handler."""

import json

import pytest

from mcp_text_editor.handlers.peek_text_file_contents import PeekTextFileContentsHandler
from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def peek_handler():
    """Create an instance of PeekTextFileContentsHandler."""
    handler = PeekTextFileContentsHandler()
    handler.editor = TextEditor()
    return handler


@pytest.fixture
def temp_files(tmpdir):
    """Create temporary text files for testing."""
    # Create a text file with a known number of lines
    file1 = tmpdir.join("file1.txt")
    with open(file1, "w") as f:
        f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n" * 5)

    # Create a longer text file
    file2 = tmpdir.join("file2.txt")
    with open(file2, "w") as f:
        f.write("Test line\n" * 50)

    # Create a binary file
    binary_file = tmpdir.join("binary.bin")
    with open(binary_file, "wb") as f:
        f.write(bytes([0x00, 0x01, 0x02, 0x03]))

    # Create an empty file
    empty_file = tmpdir.join("empty.txt")
    empty_file.write("")

    return {
        "file1": str(file1),
        "file2": str(file2),
        "binary_file": str(binary_file),
        "empty_file": str(empty_file),
        "nonexistent_file": str(tmpdir.join("nonexistent.txt")),
    }


async def test_peek_handler_tool_description(peek_handler):
    """Test that the tool description is properly formatted."""
    tool_desc = peek_handler.get_tool_description()

    assert tool_desc.name == "peek_text_file_contents"
    assert "file_paths" in tool_desc.inputSchema["properties"]
    assert tool_desc.inputSchema["required"] == ["file_paths"]


async def test_peek_single_file(peek_handler, temp_files):
    """Test peeking at a single file."""
    args = {
        "file_paths": [temp_files["file1"]],
        "num_lines": 5,
        "encoding": "utf-8",
    }

    result = await peek_handler.run_tool(args)
    assert len(result) == 1

    data = json.loads(result[0].text)
    file_result = data[temp_files["file1"]]

    assert file_result["result"] == "ok"
    assert file_result["num_lines_peeked"] == 5
    assert file_result["total_lines"] == 25
    assert len(file_result["lines"]) == 5
    assert "peek_hash" in file_result
    assert "file_hash" in file_result


async def test_peek_multiple_files(peek_handler, temp_files):
    """Test peeking at multiple files."""
    args = {
        "file_paths": [temp_files["file1"], temp_files["file2"]],
        "num_lines": 3,
        "encoding": "utf-8",
    }

    result = await peek_handler.run_tool(args)
    data = json.loads(result[0].text)

    # Check both files are in the result
    assert temp_files["file1"] in data
    assert temp_files["file2"] in data

    # Check each file has the expected structure
    for file_path in [temp_files["file1"], temp_files["file2"]]:
        file_result = data[file_path]
        assert file_result["result"] == "ok"
        assert file_result["num_lines_peeked"] == 3
        assert len(file_result["lines"]) == 3
        assert "peek_hash" in file_result
        assert "file_hash" in file_result


async def test_peek_empty_file(peek_handler, temp_files):
    """Test peeking at an empty file."""
    args = {
        "file_paths": [temp_files["empty_file"]],
        "num_lines": 10,
        "encoding": "utf-8",
    }

    result = await peek_handler.run_tool(args)
    data = json.loads(result[0].text)
    file_result = data[temp_files["empty_file"]]

    assert file_result["result"] == "ok"
    assert file_result["num_lines_peeked"] == 0
    assert file_result["total_lines"] == 0
    assert len(file_result["lines"]) == 0
    assert file_result["peek_hash"] == file_result["file_hash"]


async def test_peek_binary_file(peek_handler, temp_files):
    """Test error handling when peeking at a binary file."""
    args = {
        "file_paths": [temp_files["binary_file"]],
        "num_lines": 10,
        "encoding": "utf-8",
    }

    result = await peek_handler.run_tool(args)
    data = json.loads(result[0].text)
    file_result = data[temp_files["binary_file"]]

    assert file_result["result"] == "error"
    assert "binary file" in file_result["reason"].lower()


async def test_peek_nonexistent_file(peek_handler, temp_files):
    """Test error handling when peeking at a nonexistent file."""
    args = {
        "file_paths": [temp_files["nonexistent_file"]],
        "num_lines": 10,
        "encoding": "utf-8",
    }

    result = await peek_handler.run_tool(args)
    data = json.loads(result[0].text)
    file_result = data[temp_files["nonexistent_file"]]

    assert file_result["result"] == "error"
    assert "does not exist" in file_result["reason"].lower()


async def test_peek_all_files(peek_handler, temp_files):
    """Test peeking at files with different properties."""
    args = {
        "file_paths": [
            temp_files["file1"],
            temp_files["empty_file"],
            temp_files["nonexistent_file"],
            temp_files["binary_file"],
        ],
        "num_lines": 10,
        "encoding": "utf-8",
    }

    result = await peek_handler.run_tool(args)
    data = json.loads(result[0].text)

    # Check that all files are in the result
    for file_path in temp_files.values():
        if file_path in data:  # Skip the directory
            assert file_path in data

    # Check each file has the appropriate result
    assert data[temp_files["file1"]]["result"] == "ok"
    assert data[temp_files["empty_file"]]["result"] == "ok"
    assert data[temp_files["nonexistent_file"]]["result"] == "error"
    assert data[temp_files["binary_file"]]["result"] == "error"
