import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class DockerSandboxManager:
    """
    Manages the lifecycle of Docker containers used for isolating
    Worker agent shell tools and file operations.
    """
    def __init__(self, image_name: str = "openclaw_worker_sandbox:latest"):
        self.image_name = image_name
        self.workspace_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "workspace"))
        
        # Ensure workspace dir exists on host so docker doesn't fail mounting it
        os.makedirs(self.workspace_dir, exist_ok=True)
        
    def _is_docker_running(self) -> bool:
        try:
            subprocess.run(["docker", "info"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def build_image_if_missing(self):
        """Builds the sandbox image if it doesn't exist."""
        if not self._is_docker_running():
            logger.warning("Docker is not running or not installed. Sandbox will be DISABLED.")
            return False

        try:
            # Check if image exists
            result = subprocess.run(
                ["docker", "image", "inspect", self.image_name],
                capture_output=True
            )
            if result.returncode != 0:
                logger.info(f"Building Docker image {self.image_name}...")
                dockerfile_dir = os.path.dirname(__file__)
                subprocess.run(
                    ["docker", "build", "-t", self.image_name, "-f", "Dockerfile.sandbox", "."],
                    cwd=dockerfile_dir,
                    check=True
                )
            return True
        except Exception as e:
            logger.error(f"Failed to build sandbox image: {e}")
            return False

    def start_sandbox(self, session_id: str) -> str:
        """
        Starts a container for a specific session. 
        Returns the container name if successful, or empty string if failed.
        """
        if not self.build_image_if_missing():
            return ""

        container_name = f"openclaw_sandbox_{session_id}"
        
        # Check if already running
        try:
            res = subprocess.run(["docker", "ps", "-q", "-f", f"name={container_name}"], capture_output=True, text=True)
            if res.stdout.strip():
                return container_name # Already running
        except Exception:
            pass

        # Try to clean up any dead container with same name
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

        try:
            logger.info(f"Starting sandbox container: {container_name}")
            subprocess.run([
                "docker", "run", "-d",
                "--name", container_name,
                "-v", f"{self.workspace_dir}:/workspace",
                self.image_name
            ], check=True, capture_output=True)
            return container_name
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start sandbox container: {e.stderr}")
            return ""

    def stop_sandbox(self, session_id: str):
        """Stops and removes the sandbox container."""
        container_name = f"openclaw_sandbox_{session_id}"
        logger.info(f"Stopping sandbox container: {container_name}")
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

    def execute_in_sandbox(self, session_id: str, command: str, timeout: int = 30) -> str:
        """Executes a command inside the sandbox container."""
        container_name = self.start_sandbox(session_id)
        if not container_name:
            return "ERROR: Sandbox is disabled or Docker failed to start."
            
        try:
            # We use `docker exec -i` so it doesn't require a TTY
            result = subprocess.run(
                ["docker", "exec", "-i", container_name, "bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Command failed with code {result.returncode}:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timed out inside sandbox."
        except Exception as e:
            return f"Error executing inside sandbox: {str(e)}"

# Global instance
sandbox_manager = DockerSandboxManager()
