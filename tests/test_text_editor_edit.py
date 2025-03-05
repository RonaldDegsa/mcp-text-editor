"""Tests for the TextEditor edit operations."""

import pytest

from mcp_text_editor.models import EditPatch
from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def editor():
    """Create TextEditor instance."""
    return TextEditor()


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file."""
    file_path = tmp_path / "test.txt"
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    file_path.write_text(content)
    return file_path


@pytest.mark.asyncio
async def test_edit_file_with_edit_patch_object(editor, tmp_path):
    """Test editing a file using EditPatch object."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n")
    file_hash = editor.calculate_hash(test_file.read_text())
    first_line_content = "line1\n"

    # Create an EditPatch object
    patch = EditPatch(
        start=1,
        end=1,
        contents="new line\n",
        range_hash=editor.calculate_hash(first_line_content),
    )

    result = await editor.edit_file_contents(str(test_file), file_hash, [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "new line\nline2\nline3\n"


@pytest.mark.asyncio
async def test_update_file(editor, tmp_path):
    """Test updating an existing file."""
    # Create a test file
    test_file = tmp_path / "test_update.txt"
    original_content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(original_content)

    # Read the content and get hash
    content, start, end, file_hash, total_lines, size = await editor.read_file_contents(
        str(test_file)
    )

    # Update the second line
    new_content = "Updated Line 2\n"
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 2,
                "end": 2,
                "contents": new_content,
                "range_hash": editor.calculate_hash("Line 2\n"),
            }
        ],
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nUpdated Line 2\nLine 3\n"


@pytest.mark.asyncio
async def test_create_new_file(editor, tmp_path):
    """Test creating a new file."""
    new_file = tmp_path / "new_file.txt"
    content = "New file content\nLine 2\n"

    # Test creating a new file
    result = await editor.edit_file_contents(
        str(new_file),
        "",  # No hash for new file
        [
            {"start": 1, "contents": content, "range_hash": ""}
        ],  # Empty range_hash for new files
    )
    assert result["result"] == "ok"
    assert new_file.read_text() == content


@pytest.mark.asyncio
async def test_create_file_in_new_directory(editor, tmp_path):
    """Test creating a file in a new directory structure."""
    # Test file in a new directory structure
    new_file = tmp_path / "subdir" / "nested" / "test.txt"
    content = "Content in nested directory\n"

    result = await editor.edit_file_contents(
        str(new_file),
        "",  # No hash for new file
        [
            {"start": 1, "contents": content, "range_hash": ""}
        ],  # Empty range_hash for new file
    )

    assert result["result"] == "ok"
    assert new_file.read_text() == content


@pytest.mark.asyncio
async def test_file_hash_mismatch(editor, tmp_path):
    """Test handling of file hash mismatch."""
    # Create a test file
    test_file = tmp_path / "test_hash_mismatch.txt"
    original_content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(original_content)

    result = await editor.edit_file_contents(
        str(test_file),
        "invalid_hash",  # Wrong hash
        [
            {
                "start": 2,
                "end": 2,
                "contents": "Updated Line\n",
                "range_hash": editor.calculate_hash("Line 2\n"),
            }
        ],
    )

    assert result["result"] == "error"
    assert "hash mismatch" in result["reason"].lower()
    assert test_file.read_text() == original_content  # File should remain unchanged


@pytest.mark.asyncio
async def test_overlapping_patches(editor, tmp_path):
    """Test handling of overlapping patches."""
    # Create a test file
    test_file = tmp_path / "test_overlap.txt"
    original_content = "Line 1\nLine 2\nLine 3\nLine 4\n"
    test_file.write_text(original_content)

    # Get file hash
    content, start, end, file_hash, total_lines, size = await editor.read_file_contents(
        str(test_file)
    )

    # Try to apply overlapping patches
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 1,
                "end": 2,
                "contents": "New Line 1-2\n",
                "range_hash": editor.calculate_hash("Line 1\nLine 2\n"),
            },
            {
                "start": 2,
                "end": 3,
                "contents": "New Line 2-3\n",
                "range_hash": editor.calculate_hash("Line 2\nLine 3\n"),
            },
        ],
    )

    assert result["result"] == "error"
    assert "overlap" in result["reason"].lower()
    assert test_file.read_text() == original_content  # File should remain unchanged


@pytest.mark.asyncio
async def test_directory_creation_error(editor, tmp_path, mocker):
    """Test file creation when parent directory creation fails."""
    test_dir = tmp_path / "test_dir"
    test_file = test_dir / "test.txt"

    # Mock os.makedirs to raise an OSError
    mocker.patch("os.makedirs", side_effect=OSError("Permission denied"))

    result = await editor.edit_file_contents(
        str(test_file), "", [EditPatch(contents="test content\n", range_hash="")]
    )

    assert result["result"] == "error"
    assert "Failed to create directory" in result["reason"]
    assert result["file_hash"] is None


@pytest.mark.asyncio
async def test_edit_file_with_none_line_end(editor, tmp_path):
    """Test editing file with end=None."""
    test_file = tmp_path / "none_end.txt"
    test_file.write_text("line1\nline2\nline3\n")

    # Get file hash
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    # Test replacement with None as end
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 2,
                "end": 3,  # Replace lines 2 and 3
                "contents": "new2\nnew3\n",
                "range_hash": editor.calculate_hash("line2\nline3\n"),
            }
        ],
    )
    assert result["result"] == "ok"
    assert test_file.read_text() == "line1\nnew2\nnew3\n"


@pytest.mark.asyncio
async def test_edit_file_with_exceeding_line_end(editor, tmp_path):
    """Test editing file with end exceeding file length."""
    test_file = tmp_path / "exceed_end.txt"
    test_file.write_text("line1\nline2\nline3\n")

    # Get file hash
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    # Test replacement with end > file length
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 2,
                "end": 10,  # File only has 3 lines
                "contents": "new2\nnew3\n",
                "range_hash": editor.calculate_hash("line2\nline3\n"),
            }
        ],
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "line1\nnew2\nnew3\n"


@pytest.mark.asyncio
async def test_new_file_with_non_empty_hash(editor, tmp_path):
    """Test handling of new file creation with non-empty hash."""
    new_file = tmp_path / "nonexistent.txt"
    result = await editor.edit_file_contents(
        str(new_file),
        "non_empty_hash",  # Non-empty hash for non-existent file
        [{"start": 1, "contents": "test content\n", "range_hash": ""}],
    )

    # Verify proper error handling
    assert result["result"] == "error"
    assert result["file_hash"] is None


@pytest.mark.asyncio
async def test_insert_operation(editor, tmp_path):
    """Test file insertion operations."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n")

    # Get file hash
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    # Test insertion operation (inserting at line 2)
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 2,
                "end": None,  # For insertion mode (empty range_hash), end is optional
                "contents": "new line\n",
                "range_hash": "",  # Empty range_hash means insertion mode
            }
        ],
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "line1\nnew line\nline2\nline3\n"


@pytest.mark.asyncio
async def test_content_without_newline(editor, tmp_path):
    """Test handling content without trailing newline."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n")

    # Get file hash
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    # Update with content that doesn't have a trailing newline
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 2,
                "end": 2,
                "contents": "new line",  # No trailing newline
                "range_hash": editor.calculate_hash("line2\n"),
            }
        ],
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "line1\nnew line\nline3\n"


@pytest.mark.asyncio
async def test_invalid_line_range(editor, tmp_path):
    """Test handling of invalid line range where end line is less than start line."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n")

    # Try to edit with invalid line range
    content, _, _, file_hash, _, _ = await editor.read_file_contents(str(test_file))

    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": 3,
                "end": 2,
                "contents": "new content\n",
                "range_hash": editor.calculate_hash("line3\n"),
            }
        ],
    )

    assert result["result"] == "error"
    assert "End line must be greater than or equal to start line" in result["reason"]


@pytest.mark.asyncio
async def test_append_mode(editor, tmp_path):
    """Test appending content when start exceeds total lines."""
    # Create a test file
    test_file = tmp_path / "test_append.txt"
    original_content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(original_content)

    # Read the content and get hash
    content, start, end, file_hash, total_lines, size = await editor.read_file_contents(
        str(test_file)
    )

    # Attempt to append content with start > total_lines
    append_content = "Appended Line\n"
    result = await editor.edit_file_contents(
        str(test_file),
        file_hash,
        [
            {
                "start": total_lines + 1,  # Start beyond current line count
                "contents": append_content,
                "range_hash": "",  # Empty range_hash for append mode
            }
        ],
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == original_content + append_content


@pytest.mark.asyncio
async def test_dict_patch_with_defaults(editor, tmp_path):
    """Test dictionary patch with default values."""
    test_file = tmp_path / "test.txt"
    original_content = "line1\nline2\nline3\n"
    test_file.write_text(original_content)

    # Get first line content and calculate hashes
    first_line_content, _, _, _, _, _ = await editor.read_file_contents(
        str(test_file), start=1, end=1
    )
    file_hash = editor.calculate_hash(original_content)

    # Edit using dict patch with missing optional fields
    patch = {
        "contents": "new line\n",  # Add newline to maintain file structure
        "start": 1,
        "end": 1,  # Explicitly specify end
        "range_hash": editor.calculate_hash(first_line_content),
    }
    result = await editor.edit_file_contents(str(test_file), file_hash, [patch])

    assert result["result"] == "ok"
    # Should replace line 1 when range_hash is provided
    assert test_file.read_text() == "new line\nline2\nline3\n"


@pytest.mark.asyncio
async def test_edit_file_without_end(editor, tmp_path):
    """Test editing a file using dictionary patch without end."""
    test_file = tmp_path / "test.txt"
    content = "line1\nline2\nline3\n"
    test_file.write_text(content)

    # Create a patch with minimal fields
    patch = EditPatch(
        contents="new line\n",
        start=1,
        end=1,
        range_hash=editor.calculate_hash("line1\n"),
    )

    # Calculate file hash from original content
    file_hash = editor.calculate_hash(content)

    result = await editor.edit_file_contents(str(test_file), file_hash, [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "new line\nline2\nline3\n"
