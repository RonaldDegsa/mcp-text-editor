"""Handler for line-range resource access."""

import urllib.parse
from typing import Optional, Tuple

from mcp.types import TextContent

from .base import BaseHandler
from ..service import TextEditorService


class LineRangeResourceHandler(BaseHandler):
    """Handler for accessing text file contents through URI templates."""

    def __init__(self):
        """Initialize the handler."""
        super().__init__()
        self.service = TextEditorService()

    async def handle_resource(self, uri: str) -> TextContent:
        """Handle a resource request for line-range access.

        Args:
            uri: URI in format text://{file_path}?lines={line_start}-{line_end}

        Returns:
            TextContent with the requested lines and metadata.

        Raises:
            ValueError: If the URI format is invalid.
        """
        file_path, line_start, line_end = self._parse_uri(uri)
        
        content, start, end, hash_, total_lines, size = await self.service.read_file_contents(
            file_path,
            line_start,
            line_end
        )

        return TextContent(
            text=content,
            metadata={
                'line_start': start,
                'line_end': end,
                'content_hash': hash_,
                'total_lines': total_lines,
                'content_size': size
            }
        )

    def _parse_uri(self, uri: str) -> Tuple[str, int, Optional[int]]:
        """Parse the resource URI to extract file path and line range.

        Args:
            uri: URI in format text://{file_path}?lines={line_start}-{line_end}

        Returns:
            Tuple of (file_path, line_start, line_end)

        Raises:
            ValueError: If the URI format is invalid.
        """
        try:
            parsed = urllib.parse.urlparse(uri)
            if parsed.scheme != 'text':
                raise ValueError(f"Invalid URI scheme: {parsed.scheme}")

            # Extract file path (remove leading / if present)
            file_path = parsed.path.lstrip('/')

            # Parse query parameters
            query = urllib.parse.parse_qs(parsed.query)
            if 'lines' not in query:
                raise ValueError("Missing 'lines' parameter")

            # Parse line range (format: start-end or start-)
            line_range = query['lines'][0]
            if '-' not in line_range:
                raise ValueError("Invalid line range format")

            start_str, *end_parts = line_range.split('-')
            end_str = end_parts[0] if end_parts else None

            # Convert to integers
            line_start = int(start_str) if start_str else 1
            line_end = int(end_str) if end_str else None

            if line_start < 1:
                raise ValueError("Line numbers must be positive")
            if line_end is not None and line_end < line_start:
                raise ValueError("End line must be greater than or equal to start line")

            return file_path, line_start, line_end

        except (ValueError, KeyError, IndexError) as e:
            raise ValueError(f"Invalid URI format: {str(e)}")