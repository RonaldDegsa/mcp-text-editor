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
    """Handler for appending content from one or more files to a target file without reading the source file content."""

    name = "append_text_file_from_path"
    description = (
        "Append content from source files to a target file with structured formatting."
    )

    def get_tool_description(self) -> Tool:
        """Get the tool description."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "source_file_paths": {
                        "oneOf": [
                            {
                                "type": "string",
                                "description": "Path to the source text file. File path must be absolute.",
                            },
                            {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of paths to source text files. File paths must be absolute.",
                            },
                        ],
                        "description": "Path(s) to the source text file(s). File path(s) must be absolute.",
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
                    "use_structured_format": {
                        "type": "boolean",
                        "description": "Whether to include structured information about the source files.",
                        "default": True,
                    },
                    "base_directory": {
                        "type": "string",
                        "description": "Base directory for calculating relative paths. If not provided, absolute paths will be used.",
                        "default": "",
                    },
                    "structure_template": {
                        "type": "string",
                        "description": "Template for the structure header. Available placeholders: {fileName}, {relativePath}, {fullPath}, {numberOfLinesInserted}, {dateInserted}",
                        "default": "=================================\n== {fileName}\n== {relativePath}\n== {fullPath}\n== {numberOfLinesInserted}\n== {dateInserted}\n=================================\n",
                    },
                },
                "required": [
                    "source_file_paths",
                    "target_file_path",
                    "target_file_hash",
                ],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            # Check for required arguments
            if "source_file_paths" not in arguments:
                raise RuntimeError("Missing required argument: source_file_paths")
            if "target_file_path" not in arguments:
                raise RuntimeError("Missing required argument: target_file_path")
            if "target_file_hash" not in arguments:
                raise RuntimeError("Missing required argument: target_file_hash")

            # Extract arguments with defaults
            source_file_paths = arguments["source_file_paths"]
            target_file_path = arguments["target_file_path"]
            target_file_hash = arguments["target_file_hash"]
            encoding = arguments.get("encoding", "utf-8")
            use_structured_format = arguments.get("use_structured_format", True)
            base_directory = arguments.get("base_directory", "")
            structure_template = arguments.get(
                "structure_template",
                "=================================\n== {fileName}\n== {relativePath}\n== {fullPath}\n== {numberOfLinesInserted}\n== {dateInserted}\n=================================\n",
            )

            # Handle both string and list inputs for source_file_paths
            if isinstance(source_file_paths, str):
                source_file_paths = [source_file_paths]

            # Validate paths
            if not os.path.isabs(target_file_path):
                raise RuntimeError(
                    f"Target file path must be absolute: {target_file_path}"
                )

            for source_path in source_file_paths:
                if not os.path.isabs(source_path):
                    raise RuntimeError(
                        f"Source file path must be absolute: {source_path}"
                    )

            # Check if target file exists
            if not os.path.exists(target_file_path):
                raise RuntimeError(f"Target file does not exist: {target_file_path}")

            # Check which source files exist and which don't
            valid_sources = []
            invalid_sources = []
            for source_path in source_file_paths:
                if os.path.exists(source_path) and os.path.isfile(source_path):
                    valid_sources.append(source_path)
                else:
                    invalid_sources.append(
                        {
                            "path": source_path,
                            "reason": "File does not exist or is not a file",
                        }
                    )

            if not valid_sources:
                raise RuntimeError("None of the source files exist or are valid files")

            # Use the append_text_file_from_path method from the editor
            result = await self.editor.append_text_file_from_path_batch(
                source_file_paths=valid_sources,
                target_file_path=target_file_path,
                target_file_hash=target_file_hash,
                encoding=encoding,
                use_structured_format=use_structured_format,
                base_directory=base_directory,
                structure_template=structure_template,
            )

            # Add information about invalid sources if any
            if invalid_sources:
                result["invalid_sources"] = invalid_sources

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
