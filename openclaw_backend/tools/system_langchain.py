from langchain_core.tools import tool
from tools.system_tools import notify_macos, get_clipboard, set_clipboard

@tool
def send_notification(title: str, message: str) -> str:
    """
    Sends a native macOS notification to the user's screen.
    Use this to alert the user when a long-running background task is finished.
    """
    return notify_macos(title, message)

@tool
def read_clipboard() -> str:
    """
    Reads textual content currently saved in the macOS clipboard.
    Useful when the user asks 'what is in my clipboard' or 'process the copied text'.
    """
    return get_clipboard()

@tool
def write_clipboard(text: str) -> str:
    """
    Writes text to the macOS clipboard.
    Useful for saving generated snippets so the user can paste them elsewhere.
    """
    return set_clipboard(text)
