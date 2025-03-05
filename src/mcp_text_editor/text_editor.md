**1. `create_error_response`**

- **Name:** `create_error_response`
- **Description:** Create a standardized error response.
- **Args:**
  - `error_message` (str): The error message to include
  - `content_hash` (Optional\[str], optional): Hash of the current content if available
  - `file_path` (Optional\[str], optional): File path to use as dictionary key
  - `suggestion` (Optional\[str], optional): Suggested operation type
  - `hint` (Optional\[str], optional): Hint message for users
- **Returns:** Dict\[str, Any]: Standardized error response structure
- **Raises:** None

**2. `_validate_environment`**

- **Name:** `_validate_environment`
- **Description:** Validate environment variables and setup. Can be extended to check for specific permissions or configurations.
- **Args:** None
- **Returns:** None
- **Raises:** None

**3. `_validate_file_path`**

- **Name:** `_validate_file_path`
- **Description:** Validate if file path is allowed and secure.
- **Args:**
  - `file_path` (str | os.PathLike): Path to validate
- **Returns:** None
- **Raises:**
  - `ValueError`: If path is not allowed or contains dangerous patterns

**4. `calculate_hash`**

- **Name:** `calculate_hash`
- **Description:** Calculate SHA-256 hash of content.
- **Args:**
  - `content` (str): Content to hash
- **Returns:** str: Hex digest of SHA-256 hash
- **Raises:** None

**5. `_read_file`**

- **Name:** `_read_file`
- **Description:** Read file and return lines, content, and total lines.
- **Args:**
  - `file_path` (str): Path to the file to read
  - `encoding` (str, optional): File encoding. Defaults to "utf-8"
- **Returns:** Tuple\[List\[str], str, int]: Lines, content, and total line count
- **Raises:**
  - `FileNotFoundError`: If file not found
  - `UnicodeDecodeError`: If file cannot be decoded with specified encoding

**6. `read_multiple_ranges`**

- **Name:** `read_multiple_ranges`
- **Description:** Reads multiple ranges from files specified in the input.
- **Args:**
  - `ranges` (List[Dict[str, Any]]): A list of dictionaries, where each dictionary represents a file range request.
  - `encoding` (str, optional): File encoding. Defaults to "utf-8".
- **Returns:** Dict[str, Dict[str, Any]]: A dictionary where keys are file paths and values are dictionaries containing the ranges read from the file and the file hash.
- **Raises:** None

**7. `read_file_contents`**

- **Name:** `read_file_contents`
- **Description:** Reads the content of a file within the specified range.
- **Args:**
  - `file_path` (str): The path to the file.
  - `start` (int, optional): The starting line number (1-based). Defaults to 1.
  - `end` (Optional[int], optional): The ending line number (inclusive). Defaults to None (read to end of file).
  - `encoding` (str, optional): The file encoding. Defaults to "utf-8".
- **Returns:** Tuple[str, int, int, str, int, int]: A tuple containing the content, start line number, end line number, content hash, total lines in the file, and content size.
- **Raises:**
  - `ValueError`: If the end line is less than the start line.

**8. `edit_file_contents`**

- **Name:** `edit_file_contents`
- **Description:** Edit file contents with hash-based conflict detection and multiple patches.
- **Args:**
  - `file_path` (str): Path to the file to edit
  - `expected_file_hash` (str): Expected hash of the file before editing
  - `patches` (List[Dict[str, Any]]): List of patches to apply
  - `encoding` (str, optional): File encoding. Defaults to "utf-8"
- **Returns:** Dict[str, Any]: Results of the operation
- **Raises:** None

**9. `insert_text_file_contents`**

- **Name:** `insert_text_file_contents`
- **Description:** Insert text content before or after a specific line in a file.
- **Args:**
  - `file_path` (str): Path to the file to edit
  - `file_hash` (str): Expected hash of the file before editing
  - `contents` (str): Content to insert
  - `after` (Optional[int]): Line number after which to insert content
  - `before` (Optional[int]): Line number before which to insert content
  - `encoding` (str, optional): File encoding. Defaults to "utf-8"
- **Returns:** Dict[str, Any]: Results containing: result, hash, and reason.
- **Raises:** None

**10. `delete_text_file_contents`**

- **Name:** `delete_text_file_contents`
- **Description:** Delete specified ranges from a text file with conflict detection.
- **Args:**
  - `request` (DeleteTextFileContentsRequest): The request containing file path, file hash, ranges to delete, and encoding.
- **Returns:** Dict[str, Any]: Results containing: result, hash, and reason.
- **Raises:** None
