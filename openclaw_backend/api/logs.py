import os
from fastapi import APIRouter, HTTPException
from typing import List, Dict

router = APIRouter()
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

@router.get("")
async def list_logs() -> Dict[str, List[Dict[str, str]]]:
    """Return a list of log files sorted by modification time (newest first)."""
    if not os.path.exists(LOGS_DIR):
        return {"logs": []}
    
    try:
        files = []
        for filename in os.listdir(LOGS_DIR):
            if filename.endswith(".txt"):
                filepath = os.path.join(LOGS_DIR, filename)
                # Get stats
                stats = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size_bytes": str(stats.st_size),
                    "modified_at": str(stats.st_mtime)
                })
        
        # Sort by modified time descending (newest first)
        files.sort(key=lambda x: float(x["modified_at"]), reverse=True)
        return {"logs": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list logs: {str(e)}")

@router.get("/{filename}")
async def get_log_content(filename: str) -> Dict[str, str]:
    """Return the raw plaintext content of a specific log file."""
    if not filename.endswith(".txt") or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid log filename.")
        
    filepath = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Log file not found.")
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")
