"""Base operations for TextEditor."""

import hashlib
import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class BaseTextOperations:
    """Base class for all text operations."""

    def _validate_file_path(self, file_path: str | os.PathLike) -> None:
        """Validate if file path is allowed and secure."""
        path_str = str(file_path)
        if ".." in path_str:
            raise ValueError("Path traversal not allowed")

    @staticmethod
    def calculate_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
        
    async def read_file_contents(
        self,
        file_path: str,
        start: int = 1,
        end: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> Tuple[str, int, int, str, int, int]:
        """Read file contents within specified line range.
        
        Returns:
            Tuple containing:
            - content: The file content within the range
            - start: Adjusted start line (1-based)
            - end: Adjusted end line
            - content_hash: Hash of the content
            - total_lines: Total number of lines in the file
            - content_size: Size of the content in bytes
        """
        # Read the whole file
        with open(file_path, "r", encoding=encoding) as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        
        # Adjust line numbers to 0-based index
        start_idx = max(1, start) - 1
        end_idx = total_lines if end is None else min(end, total_lines)
        
        if start_idx >= total_lines:
            # Return empty content if start is beyond file
            empty_content = ""
            empty_hash = self.calculate_hash(empty_content)
            return empty_content, start_idx + 1, start_idx + 1, empty_hash, total_lines, 0
            
        if end_idx < start_idx:
            raise ValueError("End line must be greater than or equal to start line")
            
        selected_lines = lines[start_idx:end_idx]
        content = "".join(selected_lines)
        content_hash = self.calculate_hash(content)
        content_size = len(content.encode(encoding))
        
        return (
            content,
            start_idx + 1,
            end_idx,
            content_hash,
            total_lines,
            content_size,
        )
