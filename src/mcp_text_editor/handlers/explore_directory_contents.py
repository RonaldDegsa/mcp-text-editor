"""Handler for exploring directory contents."""

import json
import logging
import os
import traceback
from typing import Any, Dict, List, Sequence

from mcp.types import TextContent, Tool

from .base import BaseHandler

logger = logging.getLogger("mcp-text-editor")


class ExploreDirectoryContentsHandler(BaseHandler):
    """Handler for exploring directory contents and listing files with hashes."""

    name = "explore_directory_contents"
    description = "List files and subdirectories in a directory with file hashes."

    def get_tool_description(self) -> Tool:
        """Get the tool description."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path to the directory to explore. Path must be absolute.",
                    },
                    "include_subdirectories": {
                        "type": "boolean",
                        "description": "Whether to include subdirectories recursively.",
                        "default": True,
                    },
                    "include_file_hashes": {
                        "type": "boolean",
                        "description": "Whether to include file hashes in the output.",
                        "default": True,
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding for calculating file hashes (default: 'utf-8')",
                        "default": "utf-8",
                    },
                },
                "required": ["directory_path"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            if "directory_path" not in arguments:
                raise RuntimeError("Missing required argument: directory_path")

            directory_path = arguments["directory_path"]
            include_subdirectories = arguments.get("include_subdirectories", True)
            include_file_hashes = arguments.get("include_file_hashes", True)
            encoding = arguments.get("encoding", "utf-8")

            if not os.path.isabs(directory_path):
                raise RuntimeError(f"Directory path must be absolute: {directory_path}")

            # Check if directory exists
            if not os.path.exists(directory_path):
                raise RuntimeError(f"Directory does not exist: {directory_path}")

            if not os.path.isdir(directory_path):
                raise RuntimeError(f"Path is not a directory: {directory_path}")

            result = {
                "directory": directory_path,
                "contents": await self._explore_directory(
                    directory_path,
                    include_subdirectories,
                    include_file_hashes,
                    encoding,
                ),
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e

    async def _explore_directory(
        self,
        directory_path: str,
        include_subdirectories: bool,
        include_file_hashes: bool,
        encoding: str,
    ) -> List[Dict[str, Any]]:
        """Explore directory and get contents with structure."""
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
                                item["hash"] = self.editor.calculate_hash(content)
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
