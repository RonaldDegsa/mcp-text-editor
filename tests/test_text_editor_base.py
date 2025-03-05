"""Tests for the base TextEditor class functionality."""

import pytest

from mcp_text_editor.models 
from mcp_text_editor.text_editor import EditPatch, TextEditor 


@pytest.fixture
def editor():
    """Create TextEditor instance."""
    return TextEditor()


@pytest.mark.asyncio
async def test_calculate_hash(editor):
    """Test hash calculation."""
    content = "test content"
    hash1 = editor.calculate_hash(content)
    hash2 = editor.calculate_hash(content)
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hash length


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file."""
    file_path = tmp_path / "test.txt"
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    file_path.write_text(content)
    return file_path


@pytest.mark.asyncio
async def test_read_file_contents(editor, test_file):
    """Test reading file contents."""
    # Test reading entire file
    content, start, end, hash_value, total_lines, size = (
        await editor.read_file_contents(str(test_file))
    )
    assert content == "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    assert start == 1
    assert end == 5
    assert isinstance(hash_value, str)
    assert total_lines == 5
    assert size == len(content)

    # Test reading specific lines
    content, start, end, hash_value, total_lines, size = (
        await editor.read_file_contents(str(test_file), start=2, end=4)
    )
    assert content == "Line 2\nLine 3\nLine 4\n"
    assert start == 2
    assert end == 4
    assert isinstance(hash_value, str)
    assert total_lines == 5  # Total lines in file should remain the same
    assert size == len(content)  # Size should match the selected content


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
async def test_encoding_error(editor, test_invalid_encoding_file):
    """Test handling of encoding errors when reading a file with incorrect encoding."""
    # Try to read Shift-JIS file with UTF-8 encoding
    with pytest.raises(UnicodeDecodeError) as excinfo:
        await editor.read_file_contents(test_invalid_encoding_file, encoding="utf-8")

    assert "Failed to decode file" in str(excinfo.value)
    assert "utf-8" in str(excinfo.value)


@pytest.mark.asyncio
async def test_read_file_contents_with_start_beyond_total(editor, tmp_path):
    """Test read_file_contents when start is beyond total lines."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n")

    # Call read_file_contents with start beyond total lines
    content, start, end, content_hash, total_lines, content_size = (
        await editor.read_file_contents(str(test_file), start=10)
    )

    # Verify empty content is returned
    assert content == ""
    assert start == 9  # start is converted to 0-based indexing
    assert end == 9
    assert content_hash == editor.calculate_hash("")
    assert total_lines == 3
    assert content_size == 0


@pytest.mark.asyncio
async def test_read_multiple_ranges_line_exceed(editor, tmp_path):
    """Test reading multiple ranges with exceeding line numbers."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(content)

    # Request ranges that exceed file length
    ranges = [
        {
            "file_path": str(test_file),
            "ranges": [{"start": 4, "end": None}, {"start": 1, "end": 2}],
        }
    ]

    result = await editor.read_multiple_ranges(ranges)

    # Check the exceeded range
    assert len(result[str(test_file)]["ranges"]) == 2
    # First range (exceeded)
    assert result[str(test_file)]["ranges"][0]["content"] == ""
    assert result[str(test_file)]["ranges"][0]["start"] == 4
    assert result[str(test_file)]["ranges"][0]["end"] == 4
    assert result[str(test_file)]["ranges"][0]["content_size"] == 0
    # Second range (normal)
    assert result[str(test_file)]["ranges"][1]["content"] == "Line 1\nLine 2\n"


@pytest.mark.asyncio
async def test_path_traversal_prevention(editor, tmp_path):
    """Test prevention of path traversal attacks."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Some content\n")
    unsafe_path = str(test_file) + "/.."  # Try to traverse up

    # Test read operation
    with pytest.raises(ValueError) as excinfo:
        await editor.read_file_contents(unsafe_path)
    assert "Path traversal not allowed" in str(excinfo.value)

    # Test write operation
    with pytest.raises(ValueError) as excinfo:
        await editor.edit_file_contents(
            unsafe_path,
            "",
            [{"start": 1, "contents": "malicious content\n", "range_hash": None}],
        )
    assert "Path traversal not allowed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_missing_range_hash(editor, test_file):
    """Test editing without required range hash."""
    _, _, _, file_hash, _, _ = await editor.read_file_contents(test_file)

    # Try to edit without range_hash
    with pytest.raises(ValueError, match="range_hash is required"):
        EditPatch(start=2, end=2, contents="New content\n", range_hash=None)

    with pytest.raises(ValueError, match="range_hash is required"):
        # Trying with missing range_hash field should also raise
        EditPatch(start=2, end=2, contents="New content\n")


@pytest.mark.asyncio
async def test_read_file_not_found_error(editor, tmp_path):
    """Test FileNotFoundError handling when reading a non-existent file."""
    non_existent_file = tmp_path / "does_not_exist.txt"

    with pytest.raises(FileNotFoundError) as excinfo:
        await editor._read_file(str(non_existent_file))

    assert "File not found:" in str(excinfo.value)
    assert str(non_existent_file) in str(excinfo.value)


def test_validate_environment():
    """Test environment validation."""
    # Currently _validate_environment is a placeholder
    # This test ensures the method exists and can be called without errors
    TextEditor()._validate_environment()


@pytest.mark.asyncio
async def test_initialization_with_environment_error(monkeypatch):
    """Test TextEditor initialization when environment validation fails."""

    def mock_validate_environment(self):
        raise EnvironmentError("Failed to validate environment")

    # Patch the _validate_environment method
    monkeypatch.setattr(TextEditor, "_validate_environment", mock_validate_environment)

    # Verify that initialization fails with the expected error
    with pytest.raises(EnvironmentError, match="Failed to validate environment"):
        TextEditor()


@pytest.mark.asyncio
async def test_empty_content_handling(editor, tmp_path):
    """Test handling of empty file content."""
    # Create an empty test file
    test_file = tmp_path / "empty.txt"
    test_file.write_text("")

    # Read empty file
    content, start, end, file_hash, total_lines, size = await editor.read_file_contents(
        str(test_file)
    )
    assert content == ""
    assert total_lines == 0
    assert size == 0
