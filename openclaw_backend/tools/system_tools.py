import subprocess
import platform
import os

_os = platform.system()  # "Windows", "Darwin", "Linux"


def notify_macos(title: str, message: str) -> str:
    """Send a native macOS notification."""
    try:
        command = f'display notification "{message}" with title "{title}"'
        subprocess.run(['osascript', '-e', command], check=True)
        return "Notification sent successfully."
    except Exception as e:
        return f"Failed to send notification: {str(e)}"


def notify_windows(title: str, message: str) -> str:
    """Send a Windows toast notification via PowerShell."""
    try:
        ps_script = (
            f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; '
            f'$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); '
            f'$texts = $xml.GetElementsByTagName("text"); '
            f'$texts[0].AppendChild($xml.CreateTextNode("{title}")) > $null; '
            f'$texts[1].AppendChild($xml.CreateTextNode("{message}")) > $null; '
            f'$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); '
            f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("GeminiClaw").Show($toast)'
        )
        subprocess.run(
            ['powershell', '-Command', ps_script],
            check=True, capture_output=True, timeout=10
        )
        return "Notification sent successfully."
    except Exception as e:
        return f"Failed to send notification: {str(e)}"


def notify_linux(title: str, message: str) -> str:
    """Send a Linux desktop notification via notify-send."""
    try:
        subprocess.run(['notify-send', title, message], check=True)
        return "Notification sent successfully."
    except Exception as e:
        return f"Failed to send notification: {str(e)}"


def send_notification(title: str, message: str) -> str:
    """Send a native desktop notification (cross-platform)."""
    if _os == "Darwin":
        return notify_macos(title, message)
    elif _os == "Windows":
        return notify_windows(title, message)
    elif _os == "Linux":
        return notify_linux(title, message)
    else:
        return f"Unsupported OS: {_os}"


def get_clipboard() -> str:
    """Read textual content from the system clipboard (cross-platform)."""
    try:
        if _os == "Darwin":
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, check=True)
            return result.stdout
        elif _os == "Windows":
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Clipboard'],
                capture_output=True, text=True, check=True, timeout=5
            )
            return result.stdout.strip()
        elif _os == "Linux":
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], capture_output=True, text=True, check=True)
            return result.stdout
        else:
            return f"Unsupported OS: {_os}"
    except Exception as e:
        return f"Failed to read clipboard: {str(e)}"


def set_clipboard(text: str) -> str:
    """Write text to the system clipboard (cross-platform)."""
    try:
        if _os == "Darwin":
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
            process.communicate(text)
        elif _os == "Windows":
            subprocess.run(
                ['powershell', '-Command', f'Set-Clipboard -Value "{text}"'],
                check=True, capture_output=True, timeout=5
            )
        elif _os == "Linux":
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, text=True)
            process.communicate(text)
        else:
            return f"Unsupported OS: {_os}"
        return "Clipboard updated successfully."
    except Exception as e:
        return f"Failed to write to clipboard: {str(e)}"
