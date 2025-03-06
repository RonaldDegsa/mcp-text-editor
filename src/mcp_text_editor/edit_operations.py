"""Edit operations for TextEditor."""

import logging
from typing import Any, Dict, List, Optional

from .base_operations import BaseTextOperations
from .models import EditPatch

logger = logging.getLogger(__name__)


class TextEditOperations(BaseTextOperations):
    """Handles text editing operations."""

    async def edit_file_contents(
        self,
        file_path: str,
        expected_file_hash: str,
        patches: List[Dict[str, Any]],
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """Edit file contents with conflict detection.

        Args:
            file_path (str): Path to the text file
            expected_file_hash (str): Expected hash of the file before editing
            patches (List[Dict[str, Any]]): List of patch operations
            encoding (str, optional): Text encoding. Defaults to "utf-8".

        Returns:
            Dict[str, Any]: Results containing:
                - result: "ok" or "error"
                - hash: New file hash if successful
                - reason: Error message if result is "error"
        """
        self._validate_file_path(file_path)

        try:
            (
                current_content,
                _,
                _,
                current_hash,
                total_lines,
                _,
            ) = await self.read_file_contents(file_path, encoding=encoding)

            # Check for conflicts
            if current_hash != expected_file_hash:
                return {
                    file_path: {
                        "result": "error",
                        "reason": "File hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                        "hash": current_hash,
                    }
                }

            # Split content into lines
            lines = current_content.splitlines(keepends=True)

            # Apply patches
            new_lines = lines.copy()
            for patch_dict in patches:
                patch = EditPatch.model_validate(patch_dict)
                start = patch.start - 1  # Convert to 0-based
                end = patch.end if patch.end is not None else len(lines)

                # Verify range hash if provided
                if patch.range_hash:
                    selected_lines = lines[start:end]
                    selected_content = "".join(selected_lines)
                    range_hash = self.calculate_hash(selected_content)

                    if range_hash != patch.range_hash:
                        return {
                            file_path: {
                                "result": "error",
                                "reason": f"Range hash mismatch for range {patch.start}-{patch.end}",
                                "hash": current_hash,
                            }
                        }

                # Apply the patch
                new_lines[start:end] = patch.contents.splitlines(keepends=True)

            # Write the modified content
            new_content = "".join(new_lines)

            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_content)

            # Calculate new hash
            new_hash = self.calculate_hash(new_content)

            return {
                file_path: {
                    "result": "ok",
                    "hash": new_hash,
                    "reason": None,
                }
            }

        except FileNotFoundError:
            return {
                file_path: {
                    "result": "error",
                    "reason": f"File not found: {file_path}",
                    "hash": None,
                }
            }
        except Exception as e:
            return {
                file_path: {
                    "result": "error",
                    "reason": f"Error editing file: {str(e)}",
                    "hash": None,
                }
            }

    async def insert_text_file_contents(
        self,
        file_path: str,
        file_hash: str,
        contents: str,
        after: Optional[int] = None,
        before: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """Insert text content before or after a specific line in a file.

        Args:
            file_path (str): Path to the file to edit
            file_hash (str): Expected hash of the file before editing
            contents (str): Content to insert
            after (Optional[int]): Line number after which to insert content
            before (Optional[int]): Line number before which to insert content
            encoding (str, optional): File encoding. Defaults to "utf-8"

        Returns:
            Dict[str, Any]: Results containing:
                - result: "ok" or "error"
                - hash: New file hash if successful
                - reason: Error message if result is "error"
        """
        if (after is None and before is None) or (
            after is not None and before is not None
        ):
            return {
                "result": "error",
                "reason": "Exactly one of 'after' or 'before' must be specified",
                "hash": None,
            }

        try:
            (
                current_content,
                _,
                _,
                current_hash,
                total_lines,
                _,
            ) = await self.read_file_contents(
                file_path,
                encoding=encoding,
            )

            if current_hash != file_hash:
                return {
                    "result": "error",
                    "reason": "File hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                    "hash": None,
                }

            # Split into lines, preserving line endings
            lines = current_content.splitlines(keepends=True)

            # Determine insertion point
            if after is not None:
                if after > total_lines:
                    return {
                        "result": "error",
                        "reason": f"Line number {after} is beyond end of file (total lines: {total_lines})",
                        "hash": None,
                    }
                insert_pos = after
            else:  # before must be set due to earlier validation
                assert before is not None
                if before > total_lines + 1:
                    return {
                        "result": "error",
                        "reason": f"Line number {before} is beyond end of file (total lines: {total_lines})",
                        "hash": None,
                    }
                insert_pos = before - 1

            # Ensure content ends with newline
            if not contents.endswith("\n"):
                contents += "\n"

            # Insert the content
            lines.insert(insert_pos, contents)

            # Join lines and write back to file
            final_content = "".join(lines)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(final_content)

            # Calculate new hash
            new_hash = self.calculate_hash(final_content)

            return {
                "result": "ok",
                "hash": new_hash,
                "reason": None,
            }

        except FileNotFoundError:
            return {
                "result": "error",
                "reason": f"File not found: {file_path}",
                "hash": None,
            }
        except Exception as e:
            return {
                "result": "error",
                "reason": str(e),
                "hash": None,
            }
