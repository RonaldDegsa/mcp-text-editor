"""MCP Text Editor Server implementation."""

import logging
import traceback
from collections.abc import Sequence
from typing import Any, List

from mcp.server import Server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    ResourceTemplate,
    TextContent,
    Tool,
)

from .handlers import (
    AppendTextFileContentsHandler,
    AppendTextFileFromPathHandler,
    CreateTextFileHandler,
    DeleteTextFileContentsHandler,
    ExploreDirectoryContentsHandler,
    GetTextFileContentsHandler,
    InsertTextFileContentsHandler,
    PatchTextFileContentsHandler,
    PeekTextFileContentsHandler,
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
append_file_from_path_handler = AppendTextFileFromPathHandler()
delete_contents_handler = DeleteTextFileContentsHandler()
insert_file_handler = InsertTextFileContentsHandler()
line_range_handler = LineRangeResourceHandler()
explore_directory_handler = ExploreDirectoryContentsHandler()
peek_file_handler = PeekTextFileContentsHandler()


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
            description="Access text files with line-range precision through the text:// URI scheme.",
        )
    ]


@app.list_resource_templates()
async def list_resource_templates() -> List[ResourceTemplate]:
    """List available resource templates."""
    return [
        ResourceTemplate(
            uri_template="text://{path}?lines={start}-{end}",
            name="Line range access",
            mime_type="text/plain",
            description="""Access specific line ranges in text files.
Parameters:
- path: Path to the text file
- start: Starting line number (1-based)
- end: Ending line number (optional, defaults to end of file)
Example: text://path/to/file.txt?lines=5-10""",
        )
    ]


# Define available prompts
PROMPTS = {
    "simple-edit": Prompt(
        name="simple-edit",
        description="Simple file editing without arguments",
    ),
    "code-implement": Prompt(
        name="code-implement",
        description="Implement or enhance code based on requirements",
        arguments=[
            PromptArgument(
                name="task",
                description="Implementation task description",
                required=True,
            ),
            PromptArgument(
                name="file_path",
                description="Target file path (existing or new)",
                required=False,
            ),
            PromptArgument(
                name="language", description="Programming language", required=False
            ),
        ],
    ),
    "fix-bug": Prompt(
        name="fix-bug",
        description="Help diagnose and fix bugs in code",
        arguments=[
            PromptArgument(
                name="issue",
                description="Description of the bug or issue",
                required=True,
            ),
            PromptArgument(
                name="file_path",
                description="Path to the file containing the bug",
                required=True,
            ),
            PromptArgument(
                name="error_message",
                description="Error message or stack trace, if available",
                required=False,
            ),
        ],
    ),
}


@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts."""
    return list(PROMPTS.values())


@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Handle prompt requests."""
    if name not in PROMPTS:
        raise ValueError(f"Prompt not found: {name}")

    if arguments is None:
        arguments = {}

    if name == "simple-edit":
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="""I need help editing a text file using the MCP text editor tools.

To use these tools effectively, follow these steps:

1. First, use the "get_text_file_contents" tool to read the file content and obtain the file hash.
2. If you want to make changes, use the appropriate tool:
   - For creating new files: "create_text_file"
   - For replacing content: "patch_text_file_contents" (requires file hash)
   - For inserting at a position: "insert_text_file_contents"
   - For adding to the end: "append_text_file_contents"
   - For adding content from another file: "append_text_file_from_path"
   - For removing content: "delete_text_file_contents"
   - For exploring directories: "explore_directory_contents"
   - For peeking at file contents: "peek_text_file_contents"

Please help me edit a file of my choice.""",
                    ),
                )
            ]
        )

    elif name == "code-implement":
        task = arguments.get("task", "[TASK]")
        file_path = arguments.get("file_path", "")
        language = arguments.get("language", "")

        file_path_text = f" in the file at {file_path}" if file_path else ""
        language_text = f" using {language}" if language else ""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""I need to implement the following{language_text}{file_path_text}:

{task}

Please help me with this implementation. Follow these steps:

1. First, read the existing code if needed using the "get_text_file_contents" tool
2. Understand the requirements and plan the implementation
3. If creating a new file:
   - Use "create_text_file" with the complete implementation
4. If modifying an existing file:
   - Use "get_text_file_contents" to get the current content and file hash
   - Use one of these tools to make changes:
     - "patch_text_file_contents" to replace sections (requires file hash and range hash)
     - "insert_text_file_contents" to add content at specific positions
     - "append_text_file_contents" to add content at the end
     - "append_text_file_from_path" to append content from another file
5. Verify the changes meet the requirements

Remember that all file paths must be absolute, and when patching files, you need the file hash and range hash for concurrency control.""",
                    ),
                ),
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text="I'll help you implement this code. Let me break this down into steps.",
                    ),
                ),
            ]
        )

    elif name == "fix-bug":
        issue = arguments.get("issue", "[ISSUE]")
        file_path = arguments.get("file_path", "[FILE_PATH]")
        error_message = arguments.get("error_message", "")

        error_text = (
            f"\nThe error message is:\n```\n{error_message}\n```"
            if error_message
            else ""
        )

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""I need help fixing a bug in the file at {file_path}.

The issue is: {issue}{error_text}

Please help me diagnose and fix this issue. Follow these steps:

1. First, read the code using "get_text_file_contents" to understand the context
2. Analyze the code and identify the potential cause of the bug
3. Come up with a fix
4. Apply the fix using:
   - "patch_text_file_contents" to replace buggy sections
   - "insert_text_file_contents" to add missing code
   - "delete_text_file_contents" to remove problematic code
5. Explain the root cause and how the fix addresses it

Remember that file paths must be absolute, and when using patch_text_file_contents, you need the file hash and range hash for each section you're modifying.""",
                    ),
                ),
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text="I'll help you fix this bug. Let me start by examining the code to understand what's happening.",
                    ),
                ),
            ]
        )

    raise ValueError("Prompt implementation not found")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools with enhanced descriptions and LLM guidance."""
    return [
        get_contents_handler.get_tool_description(),
        patch_file_handler.get_tool_description(),
        create_file_handler.get_tool_description(),
        append_file_handler.get_tool_description(),
        append_file_from_path_handler.get_tool_description(),
        delete_contents_handler.get_tool_description(),
        insert_file_handler.get_tool_description(),
        explore_directory_handler.get_tool_description(),
        peek_file_handler.get_tool_description(),
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
        elif name == append_file_from_path_handler.name:
            return await append_file_from_path_handler.run_tool(arguments)
        elif name == delete_contents_handler.name:
            return await delete_contents_handler.run_tool(arguments)
        elif name == insert_file_handler.name:
            return await insert_file_handler.run_tool(arguments)
        elif name == patch_file_handler.name:
            return await patch_file_handler.run_tool(arguments)
        elif name == explore_directory_handler.name:
            return await explore_directory_handler.run_tool(arguments)
        elif name == peek_file_handler.name:
            return await peek_file_handler.run_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except ValueError:
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Error executing command: {str(e)}") from e


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
