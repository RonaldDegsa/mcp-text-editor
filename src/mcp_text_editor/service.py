"""Core service logic for the MCP Text Editor Server."""

import datetime
import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    AppendTextFileFromPathBatchRequest,
    AppendTextFileFromPathRequest,
    DeleteTextFileContentsRequest,
    EditFileOperation,
    EditPatch,
    EditResult,
    ExploreDirectoryContentsRequest,
    FileRange,
    PeekTextFileContentsRequest,
)


class TextEditorService:
    """Service class for text file operations."""

    @staticmethod
    def calculate_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def read_file_contents(
        file_path: str,
        start: int = 1,
        end: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> Tuple[str, int, int]:
        """Read file contents within specified line range."""
        with open(file_path, "r", encoding=encoding) as f:
            lines = f.readlines()

        # Adjust line numbers to 0-based index
        start = max(1, start) - 1
        end = len(lines) if end is None else min(end, len(lines))

        selected_lines = lines[start:end]
        content = "".join(selected_lines)

        return content, start + 1, end

    @staticmethod
    def validate_patches(patches: List[EditPatch], total_lines: int) -> bool:
        """Validate patches for overlaps and bounds."""
        # Sort patches by start
        sorted_patches = sorted(patches, key=lambda x: x.start)

        prev_end = 0
        for patch in sorted_patches:
            if patch.start < 1:
                return False  # Invalid start line

            patch_end = patch.end or total_lines
            if patch_end > total_lines:
                return False  # End out of bounds

            if patch.start <= prev_end:
                return False  # Overlapping patch

            prev_end = patch_end

        return True

    def append_text_file_from_path(
        self, request: AppendTextFileFromPathRequest
    ) -> Dict[str, EditResult]:
        """Append content from source file to target file with hash validation."""
        current_hash = None
        try:
            # Check if source file exists and is readable
            try:
                with open(
                    request.source_file_path, "r", encoding=request.encoding
                ) as f:
                    pass  # Just checking if we can open it
            except FileNotFoundError:
                return {
                    request.target_file_path: EditResult(
                        result="error",
                        reason=f"Source file not found: {request.source_file_path}",
                        hash=None,
                    )
                }
            except Exception as e:
                return {
                    request.target_file_path: EditResult(
                        result="error",
                        reason=f"Error reading source file: {str(e)}",
                        hash=None,
                    )
                }

            # Read and verify target file hash
            try:
                with open(
                    request.target_file_path, "r", encoding=request.encoding
                ) as f:
                    current_content = f.read()
                    current_hash = self.calculate_hash(current_content)
            except FileNotFoundError:
                return {
                    request.target_file_path: EditResult(
                        result="error",
                        reason=f"Target file not found: {request.target_file_path}",
                        hash=None,
                    )
                }

            # Check for hash mismatch
            if current_hash != request.target_file_hash:
                return {
                    request.target_file_path: EditResult(
                        result="error",
                        reason="Target file hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                        hash=current_hash,
                    )
                }

            # Append source file content to target file
            try:
                with open(
                    request.target_file_path, "a", encoding=request.encoding
                ) as target_file:
                    with open(
                        request.source_file_path, "r", encoding=request.encoding
                    ) as source_file:
                        content = source_file.read()
                        if content and not content.endswith("\n"):
                            content += "\n"
                        target_file.write(content)

                # Calculate new hash
                with open(
                    request.target_file_path, "r", encoding=request.encoding
                ) as f:
                    updated_content = f.read()
                    new_hash = self.calculate_hash(updated_content)

                return {
                    request.target_file_path: EditResult(
                        result="ok",
                        hash=new_hash,
                        reason=None,
                    )
                }
            except Exception as e:
                return {
                    request.target_file_path: EditResult(
                        result="error",
                        reason=f"Error appending file: {str(e)}",
                        hash=current_hash,
                    )
                }

        except Exception as e:
            return {
                request.target_file_path: EditResult(
                    result="error",
                    reason=f"Unexpected error: {str(e)}",
                    hash=current_hash,
                )
            }

    def append_text_file_from_path_batch(
        self, request: AppendTextFileFromPathBatchRequest
    ) -> Dict[str, Any]:
        """Append content from multiple source files to target file with structured formatting."""
        current_hash = None
        try:
            # Read and verify target file hash
            try:
                with open(
                    request.target_file_path, "r", encoding=request.encoding
                ) as f:
                    current_content = f.read()
                    current_hash = self.calculate_hash(current_content)
            except FileNotFoundError:
                return {
                    "result": "error",
                    "reason": f"Target file not found: {request.target_file_path}",
                    "hash": None,
                }

            # Check for hash mismatch
            if current_hash != request.target_file_hash:
                return {
                    "result": "error",
                    "reason": "Target file hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                    "hash": current_hash,
                }

            # Append source files content to target file
            try:
                appended_files = []
                current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open(
                    request.target_file_path, "a", encoding=request.encoding
                ) as target_file:
                    for source_file_path in request.source_file_paths:
                        # Skip if source file doesn't exist
                        if not os.path.exists(source_file_path) or not os.path.isfile(
                            source_file_path
                        ):
                            appended_files.append(
                                {
                                    "path": source_file_path,
                                    "result": "error",
                                    "reason": "File does not exist or is not a file",
                                }
                            )
                            continue

                        try:
                            # Count lines in the source file
                            with open(
                                source_file_path, "r", encoding=request.encoding
                            ) as source_file:
                                source_lines = list(source_file)
                                line_count = len(source_lines)

                            file_info = {
                                "path": source_file_path,
                                "result": "ok",
                                "lines_appended": line_count,
                                "date_appended": current_date,
                            }

                            # Add structured header if requested
                            if request.use_structured_format:
                                file_name = os.path.basename(source_file_path)
                                relative_path = source_file_path

                                # Calculate relative path if base directory is provided
                                if request.base_directory and os.path.isdir(
                                    request.base_directory
                                ):
                                    try:
                                        relative_path = os.path.relpath(
                                            source_file_path, request.base_directory
                                        )
                                    except ValueError:
                                        # Fall back to absolute path if relpath fails
                                        relative_path = source_file_path

                                # Format the structured header
                                header = request.structure_template.format(
                                    fileName=file_name,
                                    relativePath=relative_path,
                                    fullPath=source_file_path,
                                    numberOfLinesInserted=line_count,
                                    dateInserted=current_date,
                                )

                                target_file.write(header)

                            # Append the source file content
                            with open(
                                source_file_path, "r", encoding=request.encoding
                            ) as source_file:
                                content = source_file.read()
                                target_file.write(content)

                                # Ensure the file ends with a newline
                                if content and not content.endswith("\n"):
                                    target_file.write("\n")

                            appended_files.append(file_info)
                        except Exception as e:
                            appended_files.append(
                                {
                                    "path": source_file_path,
                                    "result": "error",
                                    "reason": f"Error appending file: {str(e)}",
                                }
                            )

                # Calculate new hash
                with open(
                    request.target_file_path, "r", encoding=request.encoding
                ) as f:
                    updated_content = f.read()
                    new_hash = self.calculate_hash(updated_content)

                return {
                    "result": "ok",
                    "hash": new_hash,
                    "target_file": request.target_file_path,
                    "files_appended": appended_files,
                }
            except Exception as e:
                return {
                    "result": "error",
                    "reason": f"Error appending files: {str(e)}",
                    "hash": current_hash,
                }

        except Exception as e:
            return {
                "result": "error",
                "reason": f"Unexpected error: {str(e)}",
                "hash": current_hash,
            }

    def edit_file_contents(
        self, file_path: str, operation: EditFileOperation
    ) -> Dict[str, EditResult]:
        """Edit file contents with conflict detection."""
        current_hash = None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_content = f.read()
                current_hash = self.calculate_hash(current_content)

            # Check for conflicts
            if current_hash != operation.hash:
                return {
                    file_path: EditResult(
                        result="error",
                        reason="File hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                        hash=current_hash,
                    )
                }

            # Split content into lines
            lines = current_content.splitlines(keepends=True)

            # Validate patches
            if not self.validate_patches(operation.patches, len(lines)):
                return {
                    file_path: EditResult(
                        result="error",
                        reason="Invalid or overlapping patches",
                        hash=current_hash,
                    )
                }

            # Apply patches
            new_lines = lines.copy()
            for patch in operation.patches:
                start = patch.start - 1  # Convert to 0-based
                end = patch.end if patch.end is not None else len(lines)
                new_lines[start:end] = patch.contents.splitlines(keepends=True)

            # Write new content
            new_content = "".join(new_lines)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            new_hash = self.calculate_hash(new_content)
            return {
                file_path: EditResult(
                    result="ok",
                    hash=new_hash,
                    reason=None,
                )
            }

        except FileNotFoundError as e:
            return {
                file_path: EditResult(
                    result="error",
                    reason=str(e),
                    hash=None,
                )
            }
        except Exception as e:
            return {
                file_path: EditResult(
                    result="error",
                    reason=str(e),
                    hash=None,
                )
            }

    def delete_text_file_contents(
        self,
        request: DeleteTextFileContentsRequest,
    ) -> Dict[str, EditResult]:
        """Delete specified ranges from a text file with conflict detection."""
        current_hash = None
        try:
            with open(request.file_path, "r", encoding=request.encoding) as f:
                current_content = f.read()
                current_hash = self.calculate_hash(current_content)

            # Check for conflicts
            if current_hash != request.file_hash:
                return {
                    request.file_path: EditResult(
                        result="error",
                        reason="File hash mismatch - Please use get_text_file_contents tool to get current content and hash",
                        hash=current_hash,
                    )
                }

            # Split content into lines
            lines = current_content.splitlines(keepends=True)

            # Validate ranges
            if not request.ranges:
                return {
                    request.file_path: EditResult(
                        result="error",
                        reason="No ranges specified",
                        hash=current_hash,
                    )
                }

            if not self.validate_ranges(request.ranges, len(lines)):
                return {
                    request.file_path: EditResult(
                        result="error",
                        reason="Invalid or overlapping ranges",
                        hash=current_hash,
                    )
                }

            # Apply deletions in reverse order to maintain line numbers
            sorted_ranges = sorted(request.ranges, key=lambda x: x.start, reverse=True)

            for range_spec in sorted_ranges:
                start = range_spec.start - 1  # Convert to 0-based
                end = range_spec.end if range_spec.end is not None else len(lines)

                # Verify range hash if provided
                if range_spec.range_hash:
                    selected_lines = lines[start:end]
                    selected_content = "".join(selected_lines)
                    range_hash = self.calculate_hash(selected_content)

                    if range_hash != range_spec.range_hash:
                        return {
                            request.file_path: EditResult(
                                result="error",
                                reason=f"Range hash mismatch for range {range_spec.start}-{range_spec.end}",
                                hash=current_hash,
                            )
                        }

                # Delete the lines
                del lines[start:end]

            # Write the modified content
            new_content = "".join(lines)
            with open(request.file_path, "w", encoding=request.encoding) as f:
                f.write(new_content)

            # Calculate new hash
            new_hash = self.calculate_hash(new_content)

            return {
                request.file_path: EditResult(
                    result="ok",
                    hash=new_hash,
                    reason=None,
                )
            }

        except FileNotFoundError as e:
            return {
                request.file_path: EditResult(
                    result="error",
                    reason=str(e),
                    hash=None,
                )
            }
        except Exception as e:
            return {
                request.file_path: EditResult(
                    result="error",
                    reason=str(e),
                    hash=None,
                )
            }

    @staticmethod
    def validate_ranges(ranges: List[FileRange], total_lines: int) -> bool:
        """Validate ranges for overlaps and bounds."""
        # Sort ranges by start
        sorted_ranges = sorted(ranges, key=lambda x: x.start)

        prev_end = 0
        for range_spec in sorted_ranges:
            if range_spec.start < 1:
                return False  # Invalid start line

            range_end = range_spec.end or total_lines
            if range_end > total_lines:
                return False  # End out of bounds

            if range_spec.start <= prev_end:
                return False  # Overlapping range

            prev_end = range_end

        return True

    def explore_directory_contents(
        self,
        request: ExploreDirectoryContentsRequest,
    ) -> Dict[str, Any]:
        """Explore directory contents and list files with optional hash calculation."""
        try:
            if not os.path.exists(request.directory_path):
                return {
                    "result": "error",
                    "reason": f"Directory does not exist: {request.directory_path}",
                }

            if not os.path.isdir(request.directory_path):
                return {
                    "result": "error",
                    "reason": f"Path is not a directory: {request.directory_path}",
                }

            result = {
                "result": "ok",
                "directory": request.directory_path,
                "contents": self._explore_directory(
                    request.directory_path,
                    request.include_subdirectories,
                    request.include_file_hashes,
                    request.encoding,
                ),
            }

            return result

        except Exception as e:
            return {
                "result": "error",
                "reason": f"Error exploring directory: {str(e)}",
            }

    def _explore_directory(
        self,
        directory_path: str,
        include_subdirectories: bool,
        include_file_hashes: bool,
        encoding: str,
    ) -> List[Dict[str, Any]]:
        """Explore directory recursively and collect file/directory information."""
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
                        item["contents"] = self._explore_directory(
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

    def peek_text_file_contents(
        self,
        request: PeekTextFileContentsRequest,
    ) -> Dict[str, Any]:
        """Peek at the first few lines of text files."""
        results = {}

        for file_path in request.file_paths:
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
                with open(file_path, "r", encoding=request.encoding) as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= request.num_lines:
                            break
                        lines.append(line)

                # Get file stats
                file_stats = os.stat(file_path)
                total_size = file_stats.st_size

                # Count total lines in file
                total_lines = 0
                with open(file_path, "r", encoding=request.encoding) as f:
                    for _ in f:
                        total_lines += 1

                # Calculate content hash of the peeked portion
                peeked_content = "".join(lines)
                peek_hash = self.calculate_hash(peeked_content)

                # Calculate full file hash
                with open(file_path, "r", encoding=request.encoding) as f:
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
                    "reason": f"Could not decode file with {request.encoding} encoding. Possibly a binary file.",
                }
            except Exception as e:
                results[file_path] = {
                    "result": "error",
                    "reason": f"Error reading file: {str(e)}",
                }

        return results
