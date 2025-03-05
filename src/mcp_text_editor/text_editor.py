"""Core text editor functionality with file operation handling."""

import hashlib
import logging
import os
from typing import Any, Dict, List, Optional

from .delete_operations import TextDeleteOperations
from .edit_operations import TextEditOperations
from .file_operations import TextFileOperations
from .service import TextEditorService

logger = logging.getLogger(__name__)


class TextEditor(TextFileOperations, TextEditOperations, TextDeleteOperations):
    """Handles text file operations with security checks and conflict detection."""

    def __init__(self):
        """Initialize TextEditor."""
        self._validate_environment()
        self.service = TextEditorService()

    def create_error_response(
        self,
        error_message: str,
        content_hash: Optional[str] = None,
        file_path: Optional[str] = None,
        suggestion: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        error_response = {
            "result": "error",
            "reason": error_message,
            "file_hash": content_hash,
        }

        if content_hash is not None:
            error_response["file_hash"] = content_hash
        if suggestion:
            error_response["suggestion"] = suggestion
        if hint:
            error_response["hint"] = hint

        if file_path:
            return {file_path: error_response}
        return error_response

    async def explore_directory_contents(
        self,
        directory_path: str,
        include_subdirectories: bool = True,
        include_file_hashes: bool = True,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """Explore directory contents and list files with hashes.

        Args:
            directory_path (str): Path to the directory to explore
            include_subdirectories (bool, optional): Whether to include subdirectories recursively. Defaults to True.
            include_file_hashes (bool, optional): Whether to include file hashes. Defaults to True.
            encoding (str, optional): Text encoding for file content. Defaults to "utf-8".

        Returns:
            Dict[str, Any]: Results containing directory structure with files and optional hashes
        """
        self._validate_file_path(directory_path)

        try:
            if not os.path.isabs(directory_path):
                return self.create_error_response(
                    f"Directory path must be absolute: {directory_path}"
                )

            # Check if directory exists
            if not os.path.exists(directory_path):
                return self.create_error_response(
                    f"Directory does not exist: {directory_path}"
                )

            if not os.path.isdir(directory_path):
                return self.create_error_response(
                    f"Path is not a directory: {directory_path}"
                )

            # Get the directory contents
            contents = await self._explore_directory(
                directory_path, include_subdirectories, include_file_hashes, encoding
            )

            return {
                "result": "ok",
                "directory": directory_path,
                "contents": contents,
                "reason": None,
            }

        except Exception as e:
            logger.error(f"Error exploring directory: {str(e)}")
            return self.create_error_response(f"Error exploring directory: {str(e)}")

    async def _explore_directory(
        self,
        directory_path: str,
        include_subdirectories: bool,
        include_file_hashes: bool,
        encoding: str,
    ) -> List[Dict[str, Any]]:
        """Explore directory and return contents with structure."""
        contents = []

        try:
            with os.scandir(directory_path) as entries:
                for entry in entries:
                    item = {
                        "name": entry.name,
                        "path": entry.path,
                        "is_directory": entry.is_dir(),
                        "size": entry.stat().st_size if not entry.is_dir() else None,
                    }

                    if not entry.is_dir() and include_file_hashes:
                        try:
                            with open(entry.path, "r", encoding=encoding) as f:
                                content = f.read()
                                item["hash"] = self.calculate_hash(content)
                        except (UnicodeDecodeError, IOError):
                            # For binary files or those that can't be read with the specified encoding
                            item["hash"] = None
                            item["hash_error"] = (
                                "Could not calculate hash (possibly binary file or encoding error)"
                            )

                    if entry.is_dir() and include_subdirectories:
                        item["contents"] = await self._explore_directory(
                            entry.path,
                            include_subdirectories,
                            include_file_hashes,
                            encoding,
                        )

                    contents.append(item)

                # Sort contents: directories first, then files alphabetically
                contents.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))

                return contents
        except PermissionError:
            return [{"error": f"Permission denied accessing {directory_path}"}]
        except Exception as e:
            return [{"error": f"Error exploring directory: {str(e)}"}]

    async def peek_text_file_contents(
        self, file_paths: List[str], num_lines: int = 10, encoding: str = "utf-8"
    ) -> Dict[str, Dict[str, Any]]:
        """Peek at the first few lines of text files.

        Args:
            file_paths (List[str]): Paths to text files
            num_lines (int, optional): Number of lines to read. Defaults to 10.
            encoding (str, optional): Text encoding. Defaults to "utf-8".

        Returns:
            Dict[str, Dict[str, Any]]: Results containing peeked content for each file
        """
        results = {}

        for file_path in file_paths:
            self._validate_file_path(file_path)

            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    results[file_path] = {
                        "result": "error",
                        "reason": f"File does not exist: {file_path}",
                    }
                    continue

                if not os.path.isfile(file_path):
                    results[file_path] = {
                        "result": "error",
                        "reason": f"Path is not a file: {file_path}",
                    }
                    continue

                # Read the first N lines
                with open(file_path, "r", encoding=encoding) as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= num_lines:
                            break
                        lines.append(line)

                # Get file stats
                file_stats = os.stat(file_path)
                total_size = file_stats.st_size

                # Count total lines in file
                total_lines = 0
                with open(file_path, "r", encoding=encoding) as f:
                    for _ in f:
                        total_lines += 1

                # Calculate content hash of the peeked portion
                peeked_content = "".join(lines)
                peek_hash = self.calculate_hash(peeked_content)

                # Calculate full file hash
                with open(file_path, "r", encoding=encoding) as f:
                    full_content = f.read()
                    full_hash = self.calculate_hash(full_content)

                results[file_path] = {
                    "result": "ok",
                    "filename": os.path.basename(file_path),
                    "lines": lines,
                    "num_lines_peeked": len(lines),
                    "total_lines": total_lines,
                    "size": total_size,
                    "peek_hash": peek_hash,
                    "file_hash": full_hash,
                }

            except UnicodeDecodeError:
                results[file_path] = {
                    "result": "error",
                    "reason": f"Could not decode file with {encoding} encoding. Possibly a binary file.",
                }
            except Exception as e:
                results[file_path] = {
                    "result": "error",
                    "reason": f"Error reading file: {str(e)}",
                }

        return results

    def _validate_environment(self) -> None:
        """Validate environment variables and setup."""
        pass  # pragma: no cover

    def _validate_file_path(self, file_path: str | os.PathLike) -> None:
        """Validate if file path is allowed and secure."""
        path_str = str(file_path)
        if ".." in path_str:
            raise ValueError("Path traversal not allowed")

    @staticmethod
    def calculate_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
