**1. `PatchTextFileContentsHandler`**

- **Class:** `PatchTextFileContentsHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object describing the tool.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: A sequence of TextContent objects.
  - **Raises:** `RuntimeError`: If any required argument is missing or if an error occurs during processing.

**2. `LineRangeResourceHandler`**

- **Class:** `LineRangeResourceHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description. This handler doesn't function as a tool, but implements this method to satisfy the BaseHandler abstract class requirements.
  - **Args:** None
  - **Returns:** `Tool`: A placeholder Tool object.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments. This handler doesn't function as a tool, but implements this method to satisfy the BaseHandler abstract class requirements.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: An empty sequence of TextContent objects.
  - **Raises:** None
  - **Name:** `handle_resource`
  - **Description:** Handle a resource request for line-range access.
  - **Args:**
    - `uri` (str): URI in format text://{file_path}?lines={line_start}-{line_end}
  - **Returns:** `TextContent`: TextContent with the requested lines and metadata.
  - **Raises:** `ValueError`: If the URI format is invalid.
  - **Name:** `_parse_uri`
  - **Description:** Parse the resource URI to extract file path and line range.
  - **Args:**
    - `uri` (str): URI in format text://{file_path}?lines={line_start}-{line_end}
  - **Returns:** Tuple[str, int, Optional[int]]: Tuple of (file_path, line_start, line_end)
  - **Raises:** `ValueError`: If the URI format is invalid.

**3. `InsertTextFileContentsHandler`**

- **Class:** `InsertTextFileContentsHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object describing the tool.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: A sequence of TextContent objects.
  - **Raises:** `RuntimeError`: If any required argument is missing or if an error occurs during processing.

**4. `GetTextFileContentsHandler`**

- **Class:** `GetTextFileContentsHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object describing the tool.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: A sequence of TextContent objects.
  - **Raises:**
    - `RuntimeError`: If the 'files' argument is missing or if an error occurs during processing.
    - `KeyError`: If a required argument is missing within the 'files' data.

**5. `DeleteTextFileContentsHandler`**

- **Class:** `DeleteTextFileContentsHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object describing the tool.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: A sequence of TextContent objects.
  - **Raises:** `RuntimeError`: If any required argument is missing or if an error occurs during processing.

**6. `CreateTextFileHandler`**

- **Class:** `CreateTextFileHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object describing the tool.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: A sequence of TextContent objects.
  - **Raises:** `RuntimeError`: If any required argument is missing or if an error occurs during processing.

**7. `BaseHandler`**

- **Class:** `BaseHandler`
  - **Name:** `__init__`
  - **Description:** Initialize the handler.
  - **Args:**
    - `editor`: The text editor instance to use. If None, a new instance will be created.
  - **Returns:** None
  - **Raises:** None
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object that describes this tool, including its name, description, and input schema.
  - **Raises:** `NotImplementedError`: Subclasses must implement get_tool_description()
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments`: A dictionary of arguments passed to the tool.
  - **Returns:** `Sequence[TextContent]`: A sequence of TextContent objects containing the result of the tool execution.
  - **Raises:** `NotImplementedError`: Subclasses must implement run_tool()

**8. `AppendTextFileContentsHandler`**

- **Class:** `AppendTextFileContentsHandler`
  - **Name:** `get_tool_description`
  - **Description:** Get the tool description.
  - **Args:** None
  - **Returns:** `Tool`: A Tool object describing the tool.
  - **Raises:** None
  - **Name:** `run_tool`
  - **Description:** Execute the tool with given arguments.
  - **Args:**
    - `arguments` (Dict[str, Any]): A dictionary of arguments.
  - **Returns:** Sequence[TextContent]: A sequence of TextContent objects.
  - **Raises:** `RuntimeError`: If any required argument is missing or if an error occurs during processing.
