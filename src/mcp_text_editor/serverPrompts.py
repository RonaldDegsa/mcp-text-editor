from mcp.server import Server
from mcp.types import Prompt, PromptArgument
from typing import List
# Initialize server 
# This is just an example, the Server is started in server.py, and the @app decorators need to be used again in
app = Server("mcp-text-editor")
# Define available prompts
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