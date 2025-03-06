"""Base handler for MCP Text Editor."""

import abc
import logging
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from ..text_editor import TextEditor

logger = logging.getLogger("mcp-text-editor")
class BaseHandler(abc.ABC):
    """Base class for handlers.

    This class defines the interface that all handlers must implement.
    Subclasses should override the `get_tool_description()` and `run_tool()` methods.

    Attributes:
        name (str): The name of the tool.
        description (str): A description of the tool.
        editor (TextEditor): The text editor instance to use for operations.
    """

    name: str = ""
    description: str = ""

    def __init__(self, editor: TextEditor | None = None):
        """Initialize the handler.

        Args:
            editor: The text editor instance to use. If None, a new instance will be created.
        """
        self.editor = editor if editor is not None else TextEditor()
        logger.info(f"Initialized handler {self.name}")

    @abc.abstractmethod
    def get_tool_description(self) -> Tool:
        """Get the tool description.

        Returns:
            Tool: A Tool object that describes this tool, including its name, description,
                and input schema.

        Example:
            ```python
            def get_tool_description(self) -> Tool:
                return Tool(
                    name=self.name,
                    description=self.description,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the text file.",
                            }
                        },
                        "required": ["file_path"],
                    },
                )
            ```
        """
        raise NotImplementedError("Subclasses must implement get_tool_description()")

    @abc.abstractmethod
    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments.

        Args:
            arguments: A dictionary of arguments passed to the tool.

        Returns:
            Sequence[TextContent]: A sequence of TextContent objects containing the
                result of the tool execution.

        Raises:
            RuntimeError: If there is an error executing the tool.

        Example:
            ```python
            async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
                try:
                    # Process arguments and perform operations using self.editor
                    result = await self.editor.some_operation(arguments)
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
                except Exception as e:
                    raise RuntimeError(f"Error processing request: {str(e)}") from e
            ```
        """
        raise NotImplementedError("Subclasses must implement run_tool()")
