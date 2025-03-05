from mcp.server import Server
import mcp.types as types
from mcp import Prompt, PromptArgument
from typing import List
# Initialize server 
# This is the template to follow.
app = Server("mcp-text-editor")
# Define available prompts
PROMPTS = {
    "git-commit": types.Prompt(
        name="git-commit",
        description="Generate a Git commit message",
        arguments=[
            types.PromptArgument(
                name="changes",
                description="Git diff or description of changes",
                required=True
            )
        ],
    ),
    "explain-code": types.Prompt(
        name="explain-code",
        description="Explain how code works",
        arguments=[
            types.PromptArgument(
                name="code",
                description="Code to explain",
                required=True
            ),
            types.PromptArgument(
                name="language",
                description="Programming language",
                required=False
            )
        ],
    )
}

@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return list(PROMPTS.values())

@app.get_prompt()
async def get_prompt(
    name: str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    if name not in PROMPTS:
        raise ValueError(f"Prompt not found: {name}")

    if name == "git-commit":
        changes = arguments.get("changes") if arguments else ""
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Generate a concise but descriptive commit message "
                        f"for these changes:\n\n{changes}"
                    )
                )
            ]
        )

    if name == "explain-code":
        code = arguments.get("code") if arguments else ""
        language = arguments.get("language", "Unknown") if arguments else "Unknown"
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Explain how this {language} code works:\n\n{code}"
                    )
                )
            ]
        )

    raise ValueError("Prompt implementation not found")

@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts."""
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

@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> dict:
    """Handle prompt requests."""
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