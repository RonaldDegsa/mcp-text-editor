"""Delete operations for TextEditor."""

import logging
from typing import Any, Dict

from .models import DeleteTextFileContentsRequest

logger = logging.getLogger(__name__)


class TextDeleteOperations:
    """Handles text deletion operations."""

    async def delete_text_file_contents(
        self,
        request: DeleteTextFileContentsRequest,
    ) -> Dict[str, Any]:
        """Delete specified ranges from a text file with conflict detection.

        Args:
            request (DeleteTextFileContentsRequest): The request containing:
                - file_path: Path to the text file
                - file_hash: Expected hash of the file before editing
                - ranges: List of ranges to delete
                - encoding: Optional text encoding (default: utf-8)

        Returns:
            Dict[str, Any]: Results containing:
                - result: "ok" or "error"
                - hash: New file hash if successful
                - reason: Error message if result is "error"
        """
        self._validate_file_path(request.file_path)

        try:
            (
                current_content,
                _,
                _,
                current_hash,
                total_lines,
                _,
            ) = await self.read_file_contents(
                request.file_path,
                encoding=request.encoding or "utf-8",
            )

            # Check for conflicts
            if current_hash != request.file_hash:
                return {
                    "result": "error",
                    "reason": "File hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                    "hash": current_hash,
                }

            # Split content into lines
            lines = current_content.splitlines(keepends=True)

            # Sort ranges in reverse order to handle line number shifts
            sorted_ranges = sorted(request.ranges, key=lambda x: x.start, reverse=True)

            for range_spec in sorted_ranges:
                start = range_spec.start - 1  # Convert to 0-based
                end = range_spec.end if range_spec.end is not None else len(lines)

                # Validate range
                if start < 0 or end > len(lines) or start >= end:
                    return {
                        "result": "error",
                        "reason": f"Invalid range: {range_spec.start}-{range_spec.end}",
                        "hash": current_hash,
                    }

                # Verify range hash if provided
                if range_spec.range_hash:
                    selected_lines = lines[start:end]
                    selected_content = "".join(selected_lines)
                    range_hash = self.calculate_hash(selected_content)

                    if range_hash != range_spec.range_hash:
                        return {
                            "result": "error",
                            "reason": f"Range hash mismatch for range {range_spec.start}-{range_spec.end}",
                            "hash": current_hash,
                        }

                # Delete the range
                del lines[start:end]

            # Write updated content back to file
            new_content = "".join(lines)
            with open(
                request.file_path, "w", encoding=request.encoding or "utf-8"
            ) as f:
                f.write(new_content)

            # Calculate new hash
            new_hash = self.calculate_hash(new_content)

            return {
                "result": "ok",
                "hash": new_hash,
                "reason": None,
            }

        except FileNotFoundError:
            return {
                "result": "error",
                "reason": f"File not found: {request.file_path}",
                "hash": None,
            }
        except Exception as e:
            return {
                "result": "error",
                "reason": f"Error deleting content: {str(e)}",
                "hash": None,
            }
