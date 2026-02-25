import subprocess
import os

def notify_macos(title: str, message: str) -> str:
    """Send a native macOS notification."""
    try:
        command = f'display notification "{message}" with title "{title}"'
        subprocess.run(['osascript', '-e', command], check=True)
        return "Notification sent successfully."
    except Exception as e:
        return f"Failed to send notification: {str(e)}"

def get_clipboard() -> str:
    """Read textual content from the macOS clipboard."""
    try:
        result = subprocess.run(['pbpaste'], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"Failed to read clipboard: {str(e)}"

def set_clipboard(text: str) -> str:
    """Write text to the macOS clipboard."""
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
        process.communicate(text)
        return "Clipboard updated successfully."
    except Exception as e:
        return f"Failed to write to clipboard: {str(e)}"
