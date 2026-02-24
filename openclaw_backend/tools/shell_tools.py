import subprocess
import re
from langchain_core.tools import tool

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"drop\s+(table|database)",
    r"sudo\s+",
    r"del\s+/f",
]

@tool
def execute_shell_command(command: str) -> str:
    """Execute a simple shell command and return its output. Do not run interactive commands."""
    
    # ----------------------------------------------------
    # SECURITY SANDBOXING: Check for dangerous commands
    # ----------------------------------------------------
    command_lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower):
            return f"APPROVAL_REQUIRED: The command '{command}' contains potentially dangerous operations matching '{pattern}'. Awaiting Human-in-the-Loop authorization."
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30 # Prevent hanging
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Command failed with code {result.returncode}:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"
