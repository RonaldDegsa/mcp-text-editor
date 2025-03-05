# Implementation Tasks

## Models and Data Structures
- [x] Update models.py to standardize field names (file_path vs path)
- [ ] Add MultiFileOperation model for atomic operations
- [ ] Implement ErrorResponse model with suggestion/hint fields
- [ ] Add ResourceTemplate model for line-range access

## Server Implementation
- [x] Enhance server.py with proper MCP tool definitions
- [x] Add resource template declarations for line-range access
- [ ] Implement LLM-optimized prompts for edit workflows
- [x] Add resource handlers for line-range access

## Core Logic
- [ ] Implement AtomicFileTransaction class in service.py
- [ ] Add MultiFileCoordinator for handling multi-file operations
- [ ] Improve encoding support with auto-detection
- [ ] Add conflict visualization tools

## Text Editor Features
- [ ] Implement LineRangeResourceHandler in text_editor.py
- [ ] Add streaming line-range access support
- [ ] Create recovery snapshots system
- [ ] Implement encoding auto-detection

## Testing
- [ ] Add range validation tests
- [ ] Implement hash collision tests
- [ ] Create encoding compatibility tests
- [ ] Add atomic transaction rollback tests
- [ ] Implement error recovery scenario tests

## Documentation
- [ ] Update API documentation with new features
- [ ] Add examples for atomic multi-file operations
- [ ] Document encoding auto-detection features
- [ ] Add troubleshooting guide for common issues

## Current Task
Working on: Update models.py to standardize field names
