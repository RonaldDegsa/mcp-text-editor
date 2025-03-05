# Changelog

## [Unreleased]
### Changed
- Updated README.md to fix Python version requirements (standardized to 3.13+)
- Corrected installation instructions to use Python 3.13
- Removed duplicate Requirements section
- Updated code examples to reflect Python 3.13 syntax
- Standardized field names in models.py:
  - Changed 'path' to 'file_path' in EditFileOperation and InsertTextFileContentsRequest
  - Changed 'hash' to 'file_hash' in EditFileOperation
  - Changed 'start'/'end' to 'line_start'/'line_end' in GetTextFileContents models
- Enhanced MCP tool definitions in server.py:
  - Added detailed descriptions for each tool
  - Included LLM-optimized prompts for edit workflows
  - Added explicit input schema definitions
  - Improved error handling guidance
  - Added resource template declarations for line-range access
  - Implemented line range resource handler for URI-based file access

### Fixed
- Updated test paths in test_insert_text_file_handler.py to use Windows-style absolute paths, fixing platform-specific test failures
