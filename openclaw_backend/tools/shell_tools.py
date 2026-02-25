import subprocess
import re
from langchain_core.tools import tool
from sandbox.sandbox_manager import sandbox_manager
from core.config import settings

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
    
    # ----------------------------------------------------
    # DOCKER SANDBOX (Phase 4): 
    # If enabled, Worker shell commands run safely isolated from host
    # ----------------------------------------------------
    if settings.USE_DOCKER_SANDBOX and sandbox_manager._is_docker_running():
        # Ideally, we pass the real session_id, but tool args are simple right now.
        # We'll use a generic worker session for now.
        return sandbox_manager.execute_in_sandbox("worker_session", command)
    else:
        # Fallback to local host execution
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


def force_execute_command(command: str) -> str:
    """Execute a CTO-approved command, bypassing safety checks (HITL approved).
    This still runs inside the sandbox if enabled, protecting the host even for approved risky things, 
    unless CTO explicitly turns off sandbox in config.
    """
    if settings.USE_DOCKER_SANDBOX and sandbox_manager._is_docker_running():
        return sandbox_manager.execute_in_sandbox("worker_session", command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout if result.stdout else "(Command executed successfully with no output)"
        else:
            return f"Command failed with code {result.returncode}:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"
