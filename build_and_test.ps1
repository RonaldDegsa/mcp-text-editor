# Kill all instances of the mcp-text-editor
Stop-Process -Name "mcp-text-editor.exe" -Force
Write-Host "Killed all instances of the mcp-text-editor"

# Navigate to the project directory
cd d:\MCP\Git\mcp-text-editor
Write-Host "Navigated to the project directory"

# Clean the environment
if (Test-Path -Path .venv) {
    Remove-Item -Recurse -Force .venv
    if ($?) {
        Write-Host "Removed .venv directory"
    } else {
        Write-Host "Failed to remove .venv directory"
        exit 1
    }
}
if (Test-Path -Path dist) {
    Remove-Item -Recurse -Force dist
    if ($?) {
        Write-Host "Removed dist directory"
    } else {
        Write-Host "Failed to remove dist directory"
        exit 1
    }
}
if (Test-Path -Path *.egg-info) {
    Remove-Item -Recurse -Force *.egg-info
    if ($?) {
        Write-Host "Removed *.egg-info files"
    } else {
        Write-Host "Failed to remove *.egg-info files"
        exit 1
    }
}
if (Test-Path -Path __pycache__) {
    Remove-Item -Recurse -Force __pycache__
    if ($?) {
        Write-Host "Removed __pycache__ directory"
    } else {
        Write-Host "Failed to remove __pycache__ directory"
        exit 1
    }
}
if (Test-Path -Path src\**\__pycache__) {
    Remove-Item -Recurse -Force src\**\__pycache__
    if ($?) {
        Write-Host "Removed src\**\__pycache__ directories"
    } else {
        Write-Host "Failed to remove src\**\__pycache__ directories"
        exit 1
    }
}

if (Test-Path -Path .mypy_cache) {
    Remove-Item -Recurse .mypy_cache
    if ($?) {
        Write-Host "Removed .mypy_cache directories"
    } else {
        Write-Host "Failed to .mypy_cache directories"
        exit 1
    }
}

if (Test-Path -Path .pytest_cache) {
    Remove-Item -Recurse .mypy_cache
    if ($?) {
        Write-Host "Removed .mypy_cache directories"
    } else {
        Write-Host "Failed to .mypy_cache directories"
        exit 1
    }
}

if (Test-Path -Path tests\**\__pycache__) {
    Remove-Item -Recurse -Force tests\**\__pycache__
    if ($?) {
        Write-Host "Removed tests\**\__pycache__ directories"
    } else {
        Write-Host "Failed to remove tests\**\__pycache__ directories"
        exit 1
    }
}

# Create a new virtual environment with Python 3.13
py -3.13 -m venv .venv
if ($?) {
    Write-Host "Created new virtual environment"
} else {
    Write-Host "Failed to create new virtual environment"
    exit 1
}

# Activate the virtual environment
.\.venv\Scripts\Activate
if ($?) {
    Write-Host "Activated virtual environment"
} else {
    Write-Host "Failed to activate virtual environment"
    exit 1
}

# Install uv if not already installed
pip install uv
if ($?) {
    Write-Host "Installed uv"
} else {
    Write-Host "Failed to install uv"
    exit 1
}


# Sync dependencies using uv
uv sync --all-extras --link-mode=copy
if ($?) {
    Write-Host "Synced dependencies"
} else {
    Write-Host "Failed to sync dependencies"
    exit 1
}

# Format the code
uv run black src tests
if ($?) {
    Write-Host "Formatted code"
} else {
    Write-Host "Failed to format code"
    exit 1
}
uv run isort src tests
if ($?) {
    Write-Host "Sorted imports"
} else {
    Write-Host "Failed to sort imports"
    exit 1
}
uv run ruff check --fix src tests
if ($?) {
    Write-Host "Checked code with ruff"
} else {
    Write-Host "Failed to check code with ruff"
    exit 1
}

# Run tests
uv run pytest tests -v
if ($?) {
    Write-Host "Ran tests"
} else {
    Write-Host "Failed to run tests"
    exit 1
}

# Build the package
uv pip install -e .
if ($?) {
    Write-Host "Built package"
} else {
    Write-Host "Failed to build package"
    exit 1
}