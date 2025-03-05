"""Tests for TextEditor error handling."""

import pytest

from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def editor():
    """Create TextEditor instance."""
    return TextEditor()


@pytest.mark.asyncio
async def test_directory_creation_failure(editor, tmp_path):
    """Test failure in directory creation."""
    # Create a file in place of a directory to cause mkdir to fail
    base_dir = tmp_path / "blocked"
    base_dir.write_text("")
    test_file = base_dir / "subdir" / "test.txt"

    result = await editor.edit_file_contents(
        str(test_file),
        "",  # New file
        [{"line_start": 1, "contents": "test content\n", "range_hash": None}],
    )

    assert result["result"] == "error"
    assert "Failed to create directory" in result["reason"]
    assert result["file_hash"] is None


@pytest.fixture
def test_invalid_encoding_file(tmp_path):
    """Create a temporary file with a custom encoding to test encoding errors."""
    file_path = tmp_path / "invalid_encoding.txt"
    # Create Shift-JIS encoded file that will fail to decode with UTF-8
    test_data = bytes(
        [0x83, 0x65, 0x83, 0x58, 0x83, 0x67, 0x0A]
    )  # "テスト\n" in Shift-JIS
    with open(file_path, "wb") as f:
        f.write(test_data)
    return str(file_path)


@pytest.mark.asyncio
async def test_invalid_encoding_file_operations(editor, tmp_path):
    """Test handling of files with invalid encoding during various operations."""
    test_file = tmp_path / "invalid_encoding.txt"
    # Create a file with Shift-JIS content that will fail UTF-8 decoding
    test_data = bytes([0x83, 0x65, 0x83, 0x58, 0x83, 0x67, 0x0A])  # シフトJISのデータ
    with open(test_file, "wb") as f:
        f.write(test_data)

    # Test encoding error in file operations
    result = await editor.edit_file_contents(
        str(test_file),
        "",  # hash doesn't matter as it will fail before hash check
        [{"line_start": 1, "contents": "new content\n", "range_hash": None}],
        encoding="utf-8",
    )

    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]
    assert "decode" in result["reason"].lower()


@pytest.mark.asyncio
async def test_create_file_directory_error(editor, tmp_path, monkeypatch):
    """Test creating a file when directory creation fails."""
    # Create a path with multiple nested directories
    deep_path = tmp_path / "deeply" / "nested" / "path" / "test.txt"

    # Mock os.makedirs to raise an OSError
    def mock_makedirs(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr("os.makedirs", mock_makedirs)

    # Attempt to create a new file
    result = await editor.edit_file_contents(
        str(deep_path),
        "",  # Empty hash for new file
        [
            {
                "start": 1,
                "contents": "test content\n",
            }
        ],
    )

    # Verify proper error handling
    assert result["result"] == "error"
    assert "Failed to create directory" in result["reason"]
    assert "Permission denied" in result["reason"]
    assert result["file_hash"] is None
    assert "content" not in result


@pytest.mark.asyncio
async def test_file_write_permission_error(editor, tmp_path):
    """Test file write permission error handling."""
    # Create a test file
    test_file = tmp_path / "readonly.txt"
    test_file.write_text("original content\n")
    test_file.chmod(0o444)  # Make file read-only

    # Get file hash
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    # Attempt to modify read-only file
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 1,
                "end": 1,
                "contents": "new content\n",
                "range_hash": editor.calculate_hash("original content\n"),
            }
        ],
    )

    # Verify proper error handling
    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]
    assert "Permission" in result["reason"]
    assert result["file_hash"] is None
    assert "content" not in result

    # Clean up
    test_file.chmod(0o644)  # Restore write permission for cleanup


@pytest.mark.asyncio
async def test_io_error_handling(editor, tmp_path, monkeypatch):
    """Test handling of IO errors during file operations."""
    test_file = tmp_path / "test.txt"
    content = "test content\n"
    test_file.write_text(content)

    def mock_open(*args, **kwargs):
        raise IOError("Test IO Error")

    monkeypatch.setattr("builtins.open", mock_open)

    result = await editor.edit_file_contents(
        str(test_file),
        "",
        [{"line_start": 1, "contents": "new content\n"}],
    )

    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]
    assert "Test IO Error" in result["reason"]


@pytest.mark.asyncio
async def test_exception_handling(editor, tmp_path, monkeypatch):
    """Test handling of unexpected exceptions during file operations."""
    test_file = tmp_path / "test.txt"

    def mock_open(*args, **kwargs):
        raise Exception("Unexpected error")

    monkeypatch.setattr("builtins.open", mock_open)

    result = await editor.edit_file_contents(
        str(test_file),
        "",
        [{"line_start": 1, "contents": "new content\n"}],
    )

    assert result["result"] == "error"
    assert "Unexpected error" in result["reason"]


@pytest.mark.asyncio
async def test_create_file_directory_creation_failure(editor, tmp_path, monkeypatch):
    """Test handling of directory creation failure when creating a new file."""
    # Create a path with multiple nested directories
    deep_path = tmp_path / "deeply" / "nested" / "path" / "test.txt"

    # Mock os.makedirs to raise an OSError
    def mock_makedirs(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr("os.makedirs", mock_makedirs)

    # Attempt to create a new file
    result = await editor.edit_file_contents(
        str(deep_path),
        "",  # Empty hash for new file
        [
            {
                "line_start": 1,
                "contents": "test content\n",
            }
        ],
    )

    # Verify proper error handling
    assert result["result"] == "error"
    assert "Failed to create directory" in result["reason"]
    assert "Permission denied" in result["reason"]
    assert result["file_hash"] is None
    assert "content" not in result


@pytest.mark.asyncio
async def test_io_error_during_final_write(editor, tmp_path, monkeypatch):
    """Test handling of IO errors during final content writing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("original content\n")

    # Get file hash
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    # Mock open to raise IOError during final write
    original_open = open
    open_count = 0

    def mock_open(*args, **kwargs):
        nonlocal open_count
        open_count += 1
        if open_count > 1:  # Allow first open for reading, fail on write
            raise IOError("Failed to write file")
        return original_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    # Try to edit file with mocked write error
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 1,
                "end": 1,
                "contents": "new content\n",
                "range_hash": editor.calculate_hash("original content\n"),
            }
        ],
    )

    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]
    assert "Failed to write file" in result["reason"]
    assert test_file.read_text() == "original content\n"  # File should be unchanged
