"""
This file is kept for backward compatibility.
All tests are now auto-discovered in their respective modules:
  - tests/test_text_editor_base.py
  - tests/test_text_editor_edit.py
  - tests/test_text_editor_error_handling.py

To run all tests, simply execute: pytest
"""

# Import specific test functions from the split files
# From test_text_editor_base.py
from tests.test_text_editor_base import (
    test_calculate_hash,
    test_empty_content_handling,
    test_encoding_error,
    test_initialization_with_environment_error,
    test_missing_range_hash,
    test_path_traversal_prevention,
    test_read_file_contents,
    test_read_file_contents_with_start_beyond_total,
    test_read_file_not_found_error,
    test_read_multiple_ranges_line_exceed,
    test_validate_environment,
)

# From test_text_editor_edit.py
from tests.test_text_editor_edit import (
    test_append_mode,
    test_content_without_newline,
    test_create_file_in_new_directory,
    test_create_new_file,
    test_dict_patch_with_defaults,
    test_directory_creation_error,
    test_edit_file_with_edit_patch_object,
    test_edit_file_with_exceeding_line_end,
    test_edit_file_with_none_line_end,
    test_edit_file_without_end,
    test_file_hash_mismatch,
    test_insert_operation,
    test_invalid_line_range,
    test_new_file_with_non_empty_hash,
    test_overlapping_patches,
    test_update_file,
)

# From test_text_editor_error_handling.py
from tests.test_text_editor_error_handling import (
    test_create_file_directory_creation_failure,
    test_create_file_directory_error,
    test_directory_creation_failure,
    test_exception_handling,
    test_file_write_permission_error,
    test_invalid_encoding_file_operations,
    test_io_error_during_final_write,
    test_io_error_handling,
)

# This file now imports all tests from the split files explicitly
# This allows backward compatibility with existing test runners
# while maintaining a more organized test structure
