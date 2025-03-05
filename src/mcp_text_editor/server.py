"""MCP Text Editor Server implementation."""

import logging
import traceback
from collections.abc import Sequence
from typing import Any, List

from mcp.server import Server
from mcp.types import Resource, ResourceTemplate, TextContent, Tool, Prompt, PromptArgument

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
logging.basicConfig(level=logging.CRITICAL)
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


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources that can be accessed by clients."""
    logger.info("Listing available resources")
    return [
        Resource(
            uri="text://example.txt",
            name="Text file access",
            mime_type="text/plain",
            description="Access text files with line-range precision through the text:// URI scheme."
        )
    ]


@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts."""
    logger.info("Listing available prompts")
    return [
        Prompt(
            name="edit-file",
            description="Create or edit a text file",
            arguments=[
                PromptArgument(
                    name="file_path",
                    description="Path to the file to edit",
                    required=True
                ),
                PromptArgument(
                    name="task",
                    description="What you want to do with the file",
                    required=True
                )
            ]
        ),
        Prompt(
            name="code-review",
            description="Review code in a file",
            arguments=[
                PromptArgument(
                    name="file_path",
                    description="Path to the code file to review",
                    required=True
                )
            ]
        ),
        Prompt(
            name="summarize",
            description="Summarize the contents of a text file",
            arguments=[
                PromptArgument(
                    name="file_path",
                    description="Path to the file to summarize",
                    required=True
                )
            ]
        )
    ]


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools with enhanced descriptions and LLM guidance."""
    return [
        get_contents_handler.get_tool_description(),
        patch_file_handler.get_tool_description(),
        create_file_handler.get_tool_description(),
        append_file_handler.get_tool_description(),
        delete_contents_handler.get_tool_description(),
        insert_file_handler.get_tool_description(),
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


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> dict:
    """Handle prompt requests."""
    logger.info(f"Getting prompt: {name} with arguments {arguments}")
    
    if name == "edit-file":
        file_path = arguments.get("file_path", "[FILE_PATH]")
        task = arguments.get("task", "[TASK]")
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"I need to {task} in the file at {file_path}. Please help me with that."
                }
            ]
        }
    elif name == "code-review":
        file_path = arguments.get("file_path", "[FILE_PATH]")
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"Please review the code in {file_path}. Suggest any improvements or identify potential issues."
                }
            ]
        }
    elif name == "summarize":
        file_path = arguments.get("file_path", "[FILE_PATH]")
        return {
            "messages": [
                {
                    "role": "user", 
                    "content": f"Please summarize the contents of the file at {file_path} in a concise way."
                }
            ]
        }
    else:
        raise ValueError(f"Unknown prompt: {name}")


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
