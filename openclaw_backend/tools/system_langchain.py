from langchain_core.tools import tool
from tools.system_tools import send_notification as _send_notification, get_clipboard, set_clipboard

@tool
def send_notification(title: str, message: str) -> str:
    """
    Sends a native desktop notification (cross-platform: macOS, Windows, Linux).
    Use this to alert the user when a long-running background task is finished.
    """
    return _send_notification(title, message)

@tool
def read_clipboard() -> str:
    """
    Reads textual content currently saved in the system clipboard (cross-platform).
    Useful when the user asks 'what is in my clipboard' or 'process the copied text'.
    """
    return get_clipboard()

@tool
def write_clipboard(text: str) -> str:
    """
    Writes text to the system clipboard (cross-platform).
    Useful for saving generated snippets so the user can paste them elsewhere.
    """
    return set_clipboard(text)
