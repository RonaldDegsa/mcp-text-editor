"""MCP Text Editor Server implementation."""

import logging
import traceback
from collections.abc import Sequence
from typing import Any, List

from mcp.server import Server
from mcp.types import ResourceTemplate, TextContent, Tool

from .handlers import (
    AppendTextFileContentsHandler,
    CreateTextFileHandler,
    DeleteTextFileContentsHandler,
    GetTextFileContentsHandler,
    InsertTextFileContentsHandler,
    PatchTextFileContentsHandler,
)
from .handlers.line_range_resource_handler import LineRangeResourceHandler
from .version import __version__

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-text-editor")

app = Server("mcp-text-editor")
# Initialize handlers
get_contents_handler = GetTextFileContentsHandler()
patch_file_handler = PatchTextFileContentsHandler()
create_file_handler = CreateTextFileHandler()
append_file_handler = AppendTextFileContentsHandler()
delete_contents_handler = DeleteTextFileContentsHandler()
insert_file_handler = InsertTextFileContentsHandler()
line_range_handler = LineRangeResourceHandler()


@app.read_resource()
async def read_resource(uri: str) -> TextContent:
    """Handle resource read requests."""
    logger.info(f"Reading resource: {uri}")
    try:
        return await line_range_handler.handle_resource(uri)
    except ValueError as e:
        logger.error(f"Invalid resource URI: {str(e)}")
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Error reading resource: {str(e)}") from e



@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools with enhanced descriptions and LLM guidance."""
    return [
        Tool(
            name="get_text_file_contents",
            description="Read text files with line-range precision. Optimized for partial file access to minimize token usage.",
            input_schema=get_contents_handler.get_request_model().schema(),
            prompt="""When reading files:
1. Use line ranges to minimize token usage
2. Store returned hashes for subsequent edits
3. Handle multi-file operations efficiently
4. Consider using encoding parameter for non-UTF8 files""",
        ),
        Tool(
            name="patch_text_file_contents",
            description="Apply patches to text files with conflict detection and atomic operations.",
            input_schema=patch_file_handler.get_request_model().schema(),
            prompt="""When patching files:
1. Always get current content hash first
2. Use range_hash for conflict detection
3. Order patches from bottom to top
4. Handle encoding consistently
5. Consider atomic operations for multiple files""",
        ),
        Tool(
            name="create_text_file",
            description="Create new text files with proper encoding and error handling.",
            input_schema=create_file_handler.get_request_model().schema(),
            prompt="""When creating files:
1. Check if file exists first
2. Use appropriate encoding (default: UTF-8)
3. Ensure directory exists
4. Handle path validation""",
        ),
        Tool(
            name="append_text_file_contents",
            description="Append content to text files with hash validation.",
            input_schema=append_file_handler.get_request_model().schema(),
            prompt="""When appending:
1. Verify file exists
2. Use file_hash for conflict detection
3. Handle line endings properly
4. Consider encoding for content""",
        ),
        Tool(
            name="delete_text_file_contents",
            description="Delete content ranges from text files with validation.",
            input_schema=delete_contents_handler.get_request_model().schema(),
            prompt="""When deleting content:
1. Verify range existence
2. Use range_hash for validation
3. Handle overlapping ranges
4. Consider atomic operations""",
        ),
        Tool(
            name="insert_text_file_contents",
            description="Insert content at specific positions with proper line handling.",
            input_schema=insert_file_handler.get_request_model().schema(),
            prompt="""When inserting:
1. Validate insert position
2. Use file_hash for conflict detection
3. Handle line endings
4. Consider encoding for content""",
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls."""
    logger.info(f"Calling tool: {name}")
    try:
        if name == get_contents_handler.name:
            return await get_contents_handler.run_tool(arguments)
        elif name == create_file_handler.name:
            return await create_file_handler.run_tool(arguments)
        elif name == append_file_handler.name:
            return await append_file_handler.run_tool(arguments)
        elif name == delete_contents_handler.name:
            return await delete_contents_handler.run_tool(arguments)
        elif name == insert_file_handler.name:
            return await insert_file_handler.run_tool(arguments)
        elif name == patch_file_handler.name:
            return await patch_file_handler.run_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except ValueError:
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Error executing command: {str(e)}") from e


@app.list_resource_templates()
async def list_resource_templates() -> List[ResourceTemplate]:
    """List available resource templates."""
    return [
        ResourceTemplate(
            uri_template="text://{file_path}?lines={line_start}-{line_end}",
            name="Line range access",
            mime_type="text/plain",
            description="""Access specific line ranges in text files.
Parameters:
- file_path: Path to the text file
- line_start: Starting line number (1-based)
- line_end: Ending line number (optional, defaults to end of file)
Example: text://path/to/file.txt?lines=5-10""",
        )
    ]


async def main() -> None:
    """Main entry point for the MCP text editor server."""
    logger.info(f"Starting MCP text editor server v{__version__}")
    try:
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
