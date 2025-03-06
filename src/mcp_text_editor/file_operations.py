"""File read/write operations for TextEditor."""

import datetime
import inspect
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from .base_operations import BaseTextOperations
from .models import FileRanges

logger = logging.getLogger(__name__)


class TextFileOperations(BaseTextOperations):
    """Handles basic file operations."""

    MAX_CONTENT_LENGTH = 1000  # Maximum characters allowed in content returns

    def _truncate_content(
        self, content: Union[str, Dict, List], filename: str, line_number: int = 0
    ) -> Union[str, Dict, List]:
        """Helper method to truncate content and add warning message if it exceeds MAX_CONTENT_LENGTH."""

        def get_content_length(data: Union[str, Dict, List]) -> int:
            if isinstance(data, str):
                return len(data)
            elif isinstance(data, dict):
                return sum(len(str(v)) for v in data.values() if isinstance(v, str))
            elif isinstance(data, list):
                return sum(len(str(item)) for item in data if isinstance(item, str))
            return 0

        def get_caller_name() -> str:
            frame = inspect.currentframe()
            while frame:
                if frame.f_code.co_name != "_truncate_content":
                    return frame.f_code.co_name
                frame = frame.f_back
            return "unknown"

        content_length = get_content_length(content)

        if content_length <= self.MAX_CONTENT_LENGTH:
            return content

        truncation_message = (
            f"====== TRUNCATED {filename} ======\n"
            f"= Content return length exceeded, content length: {content_length}\n"
            f"= Line number: {line_number}\n"
            f"= Please use more granular line specific searches! The files are too big for you!\n"
            f"= Tool: {get_caller_name()}\n"
            f"====== END TRUNCATED ==========\n"
        )

        if isinstance(content, str):
            return truncation_message
        elif isinstance(content, dict):
            return {"result": "truncated", "message": truncation_message}
        elif isinstance(content, list):
            return [truncation_message]
        return content

    async def _read_file(
        self, file_path: str, encoding: str = "utf-8"
    ) -> Tuple[List[str], str, int]:
        """Read file and return lines, content, and total lines."""
        self._validate_file_path(file_path)
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            file_content = "".join(lines)
            filename = os.path.basename(file_path)
            truncated_lines = self._truncate_content(lines, filename)
            truncated_content = self._truncate_content(file_content, filename)
            return truncated_lines, truncated_content, len(lines)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File not found: {file_path}") from err
        except UnicodeDecodeError as err:
            raise UnicodeDecodeError(
                encoding,
                err.object,
                err.start,
                err.end,
                f"Failed to decode file '{file_path}' with {encoding} encoding",
            ) from err

    async def read_multiple_ranges(
        self, ranges: List[Dict[str, Any]], encoding: str = "utf-8"
    ) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for file_range_dict in ranges:
            file_range = FileRanges.model_validate(file_range_dict)
            file_path = file_range.file_path
            filename = os.path.basename(file_path)
            lines, file_content, total_lines = await self._read_file(
                file_path, encoding=encoding
            )
            file_hash = self.calculate_hash(file_content)
            result[file_path] = {"ranges": [], "file_hash": file_hash}

            for range_spec in file_range.ranges:
                start = max(1, range_spec.start) - 1
                end_value = range_spec.end
                end = (
                    min(total_lines, end_value)
                    if end_value is not None
                    else total_lines
                )

                if start >= total_lines:
                    empty_content = ""
                    result[file_path]["ranges"].append(
                        {
                            "content": empty_content,
                            "start": start + 1,
                            "end": start + 1,
                            "range_hash": self.calculate_hash(empty_content),
                            "total_lines": total_lines,
                            "content_size": 0,
                        }
                    )
                    continue

                selected_lines = lines[start:end]
                content = "".join(selected_lines)
                range_hash = self.calculate_hash(content)
                truncated_content = self._truncate_content(content, filename, start + 1)

                result[file_path]["ranges"].append(
                    {
                        "content": truncated_content,
                        "start": start + 1,
                        "end": end,
                        "range_hash": range_hash,
                        "total_lines": total_lines,
                        "content_size": len(content),
                    }
                )

        return result

    async def read_file_contents(
        self,
        file_path: str,
        start: int = 1,
        end: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> Tuple[str, int, int, str, int, int]:
        """Read file contents within specified line range."""
        # Call the base class implementation
        lines, _, total_lines = await self._read_file(file_path, encoding=encoding)

        if end is not None and end < start:
            raise ValueError("End line must be greater than or equal to start line")

        start = max(1, start) - 1
        end = total_lines if end is None else min(end, total_lines)

        if start >= total_lines:
            empty_content = ""
            empty_hash = self.calculate_hash(empty_content)
            return empty_content, start, start, empty_hash, total_lines, 0
        if end < start:
            raise ValueError("End line must be greater than or equal to start line")

        selected_lines = lines[start:end]
        content = "".join(selected_lines)
        content_hash = self.calculate_hash(content)
        content_size = len(content.encode(encoding))

        truncated_content = self._truncate_content(
            content, os.path.basename(file_path), start + 1
        )

        return (
            truncated_content,
            start + 1,
            end,
            content_hash,
            total_lines,
            content_size,
        )

    async def append_text_file_from_path(
        self,
        source_file_path: str,
        target_file_path: str,
        target_file_hash: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """Append content from a source file to a target file without reading the source file content.

        Args:
            source_file_path (str): Path to the source file
            target_file_path (str): Path to the target file
            target_file_hash (str): Expected hash of the target file before appending
            encoding (str, optional): File encoding. Defaults to "utf-8"

        Returns:
            Dict[str, Any]: Results containing:
                - result: "ok" or "error"
                - hash: New file hash if successful
                - reason: Error message if result is "error"
        """
        self._validate_file_path(source_file_path)
        self._validate_file_path(target_file_path)

        try:
            # Check if source file exists
            if not os.path.exists(source_file_path):
                return {
                    "result": "error",
                    "reason": f"Source file not found: {source_file_path}",
                    "hash": None,
                }

            # Check if target file exists
            if not os.path.exists(target_file_path):
                return {
                    "result": "error",
                    "reason": f"Target file not found: {target_file_path}",
                    "hash": None,
                }

            # Verify target file hash
            (
                _,
                _,
                _,
                current_hash,
                _,
                _,
            ) = await self.read_file_contents(
                target_file_path,
                encoding=encoding,
            )

            if current_hash != target_file_hash:
                return {
                    "result": "error",
                    "reason": "Target file hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                    "hash": None,
                }

            # Open the target file in append mode
            with open(target_file_path, "a", encoding=encoding) as target_file:
                # Open the source file and copy its content to the target file
                with open(source_file_path, "r", encoding=encoding) as source_file:
                    # Read the source file content in chunks to avoid loading large files into memory
                    chunk_size = 8192  # 8KB chunks
                    while True:
                        chunk = source_file.read(chunk_size)
                        if not chunk:
                            break
                        target_file.write(chunk)

                    # Ensure the file ends with a newline
                    if chunk and not chunk.endswith("\n"):
                        target_file.write("\n")

            # Read the updated file to calculate the new hash
            with open(target_file_path, "r", encoding=encoding) as f:
                updated_content = f.read()
                new_hash = self.calculate_hash(updated_content)
                truncated_content = self._truncate_content(
                    updated_content, os.path.basename(target_file_path)
                )

            return {
                "result": "ok",
                "hash": new_hash,
                "content": truncated_content,
                "reason": None,
            }

        except FileNotFoundError as e:
            return {
                "result": "error",
                "reason": str(e),
                "hash": None,
            }
        except (IOError, UnicodeError, PermissionError) as e:
            return {
                "result": "error",
                "reason": f"Error appending file: {str(e)}",
                "hash": None,
            }
        except Exception as e:
            import traceback

            logger.error(f"Error: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {
                "result": "error",
                "reason": f"Error: {str(e)}",
                "hash": None,
            }

    async def append_text_file_from_path_batch(
        self,
        source_file_paths: List[str],
        target_file_path: str,
        target_file_hash: str,
        encoding: str = "utf-8",
        use_structured_format: bool = True,
        base_directory: str = "",
        structure_template: str = "=================================\n== {fileName}\n== {relativePath}\n== {fullPath}\n== {numberOfLinesInserted}\n== {dateInserted}\n=================================\n",
    ) -> Dict[str, Any]:
        """Append content from multiple source files to a target file with structured formatting.

        Args:
            source_file_paths (List[str]): List of paths to the source files
            target_file_path (str): Path to the target file
            target_file_hash (str): Expected hash of the target file before appending
            encoding (str, optional): File encoding. Defaults to "utf-8"
            use_structured_format (bool, optional): Whether to include structured header. Defaults to True.
            base_directory (str, optional): Base directory for relative paths. Defaults to "".
            structure_template (str, optional): Template for structured header. Defaults to standard format.

        Returns:
            Dict[str, Any]: Results containing:
                - result: "ok" or "error"
                - hash: New file hash if successful
                - files_appended: Information about appended files
                - reason: Error message if result is "error"
        """
        self._validate_file_path(target_file_path)
        for source_path in source_file_paths:
            self._validate_file_path(source_path)

        try:
            # Check if target file exists
            if not os.path.exists(target_file_path):
                return {
                    "result": "error",
                    "reason": f"Target file not found: {target_file_path}",
                    "hash": None,
                }

            # Verify target file hash
            (
                _,
                _,
                _,
                current_hash,
                _,
                _,
            ) = await self.read_file_contents(
                target_file_path,
                encoding=encoding,
            )

            if current_hash != target_file_hash:
                return {
                    "result": "error",
                    "reason": "Target file hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                    "hash": current_hash,
                }

            # Open the target file in append mode
            with open(target_file_path, "a", encoding=encoding) as target_file:
                appended_files = []
                current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for source_file_path in source_file_paths:
                    # Skip if source file doesn't exist
                    if not os.path.exists(source_file_path) or not os.path.isfile(
                        source_file_path
                    ):
                        continue

                    try:
                        # Count lines in the source file
                        with open(
                            source_file_path, "r", encoding=encoding
                        ) as source_file:
                            source_lines = list(source_file)
                            line_count = len(source_lines)

                        file_info = {
                            "path": source_file_path,
                            "lines_appended": line_count,
                            "date_appended": current_date,
                        }

                        # Add structured header if requested
                        if use_structured_format:
                            file_name = os.path.basename(source_file_path)
                            relative_path = source_file_path

                            # Calculate relative path if base directory is provided
                            if base_directory and os.path.isdir(base_directory):
                                try:
                                    relative_path = os.path.relpath(
                                        source_file_path, base_directory
                                    )
                                except ValueError:
                                    # Fall back to absolute path if relpath fails
                                    relative_path = source_file_path

                            # Format the structured header
                            header = structure_template.format(
                                fileName=file_name,
                                relativePath=relative_path,
                                fullPath=source_file_path,
                                numberOfLinesInserted=line_count,
                                dateInserted=current_date,
                            )

                            target_file.write(header)

                        # Append the source file content
                        with open(
                            source_file_path, "r", encoding=encoding
                        ) as source_file:
                            # Read and write in chunks
                            chunk_size = 8192  # 8KB chunks
                            while True:
                                chunk = source_file.read(chunk_size)
                                if not chunk:
                                    break
                                target_file.write(chunk)

                            # Ensure the file ends with a newline
                            if source_lines and not source_lines[-1].endswith("\n"):
                                target_file.write("\n")

                        appended_files.append(file_info)
                    except Exception as e:
                        logger.error(
                            f"Error appending from {source_file_path}: {str(e)}"
                        )
                        file_info = {
                            "path": source_file_path,
                            "error": str(e),
                        }
                        appended_files.append(file_info)

            # Read the updated file to calculate the new hash
            with open(target_file_path, "r", encoding=encoding) as f:
                updated_content = f.read()
                new_hash = self.calculate_hash(updated_content)
                truncated_content = self._truncate_content(
                    updated_content, os.path.basename(target_file_path)
                )

            # Truncate any file info content if present
            for file_info in appended_files:
                if "content" in file_info:
                    file_info["content"] = self._truncate_content(
                        file_info["content"], os.path.basename(file_info["path"])
                    )

            return {
                "result": "ok",
                "hash": new_hash,
                "target_file": target_file_path,
                "files_appended": appended_files,
                "content": truncated_content,
                "reason": None,
            }

        except FileNotFoundError as e:
            return {
                "result": "error",
                "reason": str(e),
                "hash": None,
            }
        except (IOError, UnicodeError, PermissionError) as e:
            return {
                "result": "error",
                "reason": f"Error appending files: {str(e)}",
                "hash": None,
            }
        except Exception as e:
            import traceback

            logger.error(f"Error: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {
                "result": "error",
                "reason": f"Error: {str(e)}",
                "hash": None,
            }
