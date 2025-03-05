"""Handler for appending content from one file to another."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from .base import BaseHandler

logger = logging.getLogger("mcp-text-editor")


class AppendTextFileFromPathHandler(BaseHandler):
    """Handler for appending content from one file to another without reading the source file content."""

    name = "append_text_file_from_path"
    description = "Append content from a source file to a target file without reading the source file content."

    def get_tool_description(self) -> Tool:
        """Get the tool description."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "source_file_path": {
                        "type": "string",
                        "description": "Path to the source text file. File path must be absolute.",
                    },
                    "target_file_path": {
                        "type": "string",
                        "description": "Path to the target text file. File path must be absolute.",
                    },
                    "target_file_hash": {
                        "type": "string",
                        "description": "Hash of the target file contents for concurrency control. It should be matched with the file_hash when get_text_file_contents is called on the target file.",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding (default: 'utf-8')",
                        "default": "utf-8",
                    },
                },
                "required": [
                    "source_file_path",
                    "target_file_path",
                    "target_file_hash",
                ],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            if "source_file_path" not in arguments:
                raise RuntimeError("Missing required argument: source_file_path")
            if "target_file_path" not in arguments:
                raise RuntimeError("Missing required argument: target_file_path")
            if "target_file_hash" not in arguments:
                raise RuntimeError("Missing required argument: target_file_hash")

            source_file_path = arguments["source_file_path"]
            target_file_path = arguments["target_file_path"]

            if not os.path.isabs(source_file_path):
                raise RuntimeError(
                    f"Source file path must be absolute: {source_file_path}"
                )
            if not os.path.isabs(target_file_path):
                raise RuntimeError(
                    f"Target file path must be absolute: {target_file_path}"
                )

            # Check if source file exists
            if not os.path.exists(source_file_path):
                raise RuntimeError(f"Source file does not exist: {source_file_path}")

            # Check if target file exists
            if not os.path.exists(target_file_path):
                raise RuntimeError(f"Target file does not exist: {target_file_path}")

            encoding = arguments.get("encoding", "utf-8")

            # Use the append_text_file_from_path method from the editor
            result = await self.editor.append_text_file_from_path(
                source_file_path=source_file_path,
                target_file_path=target_file_path,
                target_file_hash=arguments["target_file_hash"],
                encoding=encoding,
            )

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
