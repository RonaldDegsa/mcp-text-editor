"""Handler for peeking at the beginning of text files."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from .base import BaseHandler

logger = logging.getLogger("mcp-text-editor")


class PeekTextFileContentsHandler(BaseHandler):
    """Handler for peeking at the first few lines of text files."""

    name = "peek_text_file_contents"
    description = "Read the first N lines of one or more text files."

    def get_tool_description(self) -> Tool:
        """Get the tool description."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": "List of absolute paths to text files to peek at.",
                    },
                    "num_lines": {
                        "type": "integer",
                        "description": "Number of lines to read from the beginning of each file.",
                        "default": 10,
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding (default: 'utf-8')",
                        "default": "utf-8",
                    },
                },
                "required": ["file_paths"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            if "file_paths" not in arguments:
                raise RuntimeError("Missing required argument: file_paths")

            file_paths = arguments["file_paths"]
            num_lines = arguments.get("num_lines", 10)
            encoding = arguments.get("encoding", "utf-8")

            if not isinstance(file_paths, list):
                file_paths = [file_paths]  # Convert single path to list

            if not file_paths:
                raise RuntimeError("At least one file path is required")

            for file_path in file_paths:
                if not os.path.isabs(file_path):
                    raise RuntimeError(f"File path must be absolute: {file_path}")

            results = {}
            for file_path in file_paths:
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

                    # Count total lines in file (efficient way)
                    total_lines = 0
                    with open(file_path, "r", encoding=encoding) as f:
                        for _ in f:
                            total_lines += 1

                    # Calculate content hash of the peeked portion
                    peeked_content = "".join(lines)
                    peek_hash = self.editor.calculate_hash(peeked_content)

                    # Calculate full file hash
                    with open(file_path, "r", encoding=encoding) as f:
                        full_content = f.read()
                        full_hash = self.editor.calculate_hash(full_content)

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

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
