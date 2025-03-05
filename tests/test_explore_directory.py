"""Tests for the explore_directory_contents handler."""

import json
import os

import pytest

from mcp_text_editor.handlers.explore_directory_contents import (
    ExploreDirectoryContentsHandler,
)
from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def explore_handler():
    """Create an instance of ExploreDirectoryContentsHandler."""
    handler = ExploreDirectoryContentsHandler()
    handler.editor = TextEditor()
    return handler


@pytest.fixture
def temp_dir_with_files(tmpdir):
    """Create a temporary directory structure with files for testing."""
    # Create a nested directory structure
    subdir1 = tmpdir.mkdir("subdir1")
    subdir2 = tmpdir.mkdir("subdir2")
    nested_subdir = subdir1.mkdir("nested")

    # Create some files
    tmpdir.join("file1.txt").write("Test file 1 content")
    tmpdir.join("file2.txt").write("Test file 2 content")
    subdir1.join("subdir1_file.txt").write("Subdir1 file content")
    subdir2.join("subdir2_file.txt").write("Subdir2 file content")
    nested_subdir.join("nested_file.txt").write("Nested file content")

    # Create a binary file
    with open(os.path.join(tmpdir, "binary_file.bin"), "wb") as f:
        f.write(bytes([0x00, 0x01, 0x02, 0x03]))

    return tmpdir


async def test_explore_handler_tool_description(explore_handler):
    """Test that the tool description is properly formatted."""
    tool_desc = explore_handler.get_tool_description()

    assert tool_desc.name == "explore_directory_contents"
    assert "directory_path" in tool_desc.inputSchema["properties"]
    assert tool_desc.inputSchema["required"] == ["directory_path"]


async def test_explore_directory_with_all_options(explore_handler, temp_dir_with_files):
    """Test exploring a directory with all options enabled."""
    args = {
        "directory_path": str(temp_dir_with_files),
        "include_subdirectories": True,
        "include_file_hashes": True,
        "encoding": "utf-8",
    }

    result = await explore_handler.run_tool(args)
    assert len(result) == 1

    result_json = result[0].text
    data = json.loads(result_json)

    # Check top-level structure
    assert data["directory"] == str(temp_dir_with_files)
    assert "contents" in data
    assert isinstance(data["contents"], list)

    # Check that we have all the expected files/directories
    dir_names = [item["name"] for item in data["contents"] if item["is_directory"]]
    file_names = [item["name"] for item in data["contents"] if not item["is_directory"]]

    assert "subdir1" in dir_names
    assert "subdir2" in dir_names
    assert "file1.txt" in file_names
    assert "file2.txt" in file_names
    assert "binary_file.bin" in file_names

    # Check that subdirectories have contents
    for item in data["contents"]:
        if item["is_directory"] and item["name"] == "subdir1":
            assert "contents" in item
            nested_items = item["contents"]
            nested_dirs = [nested["name"] for nested in nested_items if nested["is_directory"]]
            assert "nested" in nested_dirs


async def test_explore_directory_without_subdirectories(explore_handler, temp_dir_with_files):
    """Test exploring a directory without including subdirectories."""
    args = {
        "directory_path": str(temp_dir_with_files),
        "include_subdirectories": False,
        "include_file_hashes": True,
        "encoding": "utf-8",
    }

    result = await explore_handler.run_tool(args)
    data = json.loads(result[0].text)

    # Check that we have the top-level items but no nested contents
    for item in data["contents"]:
        if item["is_directory"]:
            assert "contents" not in item


async def test_explore_directory_without_hashes(explore_handler, temp_dir_with_files):
    """Test exploring a directory without calculating hashes."""
    args = {
        "directory_path": str(temp_dir_with_files),
        "include_subdirectories": True,
        "include_file_hashes": False,
        "encoding": "utf-8",
    }

    result = await explore_handler.run_tool(args)
    data = json.loads(result[0].text)

    # Check that no files have hashes
    for item in data["contents"]:
        if not item["is_directory"]:
            assert "hash" not in item


async def test_invalid_directory_path(explore_handler):
    """Test error handling for non-existent directory."""
    args = {
        "directory_path": "/path/that/does/not/exist",
    }

    with pytest.raises(RuntimeError, match="Directory does not exist"):
        await explore_handler.run_tool(args)


async def test_relative_path_error(explore_handler):
    """Test error handling for relative path."""
    args = {
        "directory_path": "relative/path",
    }

    with pytest.raises(RuntimeError, match="Directory path must be absolute"):
        await explore_handler.run_tool(args)


async def test_file_path_error(explore_handler, temp_dir_with_files):
    """Test error when providing a file path instead of directory."""
    test_file = temp_dir_with_files.join("file1.txt")

    args = {
        "directory_path": str(test_file),
    }

    with pytest.raises(RuntimeError, match="Path is not a directory"):
        await explore_handler.run_tool(args)
