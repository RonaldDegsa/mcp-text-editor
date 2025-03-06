"""Core text editor functionality with file operation handling."""

import logging
from typing import Any, Dict, Optional

from .delete_operations import TextDeleteOperations
from .edit_operations import TextEditOperations
from .file_operations import TextFileOperations
from .service import TextEditorService

logger = logging.getLogger(__name__)


class TextEditor(TextFileOperations, TextEditOperations, TextDeleteOperations):
    """Handles text file operations with security checks and conflict detection."""

    def __init__(self):
        """Initialize TextEditor."""
        self._validate_environment()
        self.service = TextEditorService()

    def create_error_response(
        self,
        error_message: str,
        content_hash: Optional[str] = None,
        file_path: Optional[str] = None,
        suggestion: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        error_response = {
            "result": "error",
            "reason": error_message,
            "file_hash": content_hash,
        }

        if content_hash is not None:
            error_response["file_hash"] = content_hash
        if suggestion:
            error_response["suggestion"] = suggestion
        if hint:
            error_response["hint"] = hint

        if file_path:
            return {file_path: error_response}
        return error_response

    def _validate_environment(self) -> None:
        """Validate environment variables and setup."""
        pass  # pragma: no cover
