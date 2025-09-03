# filesystem_tools.py
import os
import time
import shutil
from mcp.server.fastmcp import FastMCP as MCP

mcp = MCP("File System Tools")

BASE_DIR = os.path.abspath("./workspace")
os.makedirs(BASE_DIR, exist_ok=True)

tools = []  # collect exposed tools here


def _safe_path(path: str) -> str:
    """Ensure all file operations stay inside BASE_DIR."""
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))
    if not full_path.startswith(BASE_DIR):
        raise ValueError("Access outside sandbox is not allowed!")
    return full_path


@mcp.tool(tools)
def list_files(path: str = ".") -> dict:
    """List all files in the given directory inside the sandbox."""
    target = _safe_path(path)
    return {"files": [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]}


@mcp.tool(tools)
def read_file(path: str) -> dict:
    """Read the full content of a text file inside the sandbox."""
    target = _safe_path(path)
    with open(target, "r", encoding="utf-8") as f:
        return {"content": f.read()}


@mcp.tool(tools)
def write_file(path: str, content: str, overwrite: bool = False) -> dict:
    """Write text content to a file. Use overwrite=True to replace an existing file."""
    target = _safe_path(path)
    if os.path.exists(target) and not overwrite:
        return {"error": f"File '{path}' already exists. Use overwrite=True to replace it."}
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return {"status": f"File '{path}' written successfully."}


@mcp.tool(tools)
def delete_file(path: str) -> dict:
    """Delete a file inside the sandbox directory."""
    target = _safe_path(path)
    if not os.path.exists(target):
        return {"error": f"File '{path}' does not exist."}
    if os.path.isdir(target):
        return {"error": f"'{path}' is a directory, not a file."}
    os.remove(target)
    return {"status": f"File '{path}' deleted successfully."}


@mcp.tool(tools)
def file_info(path: str) -> dict:
    """Return metadata (size, type, last modified time) for a file or directory."""
    target = _safe_path(path)
    if not os.path.exists(target):
        return {"error": f"File '{path}' does not exist."}
    stats = os.stat(target)
    return {
        "path": path,
        "is_directory": os.path.isdir(target),
        "size_bytes": stats.st_size,
        "last_modified": time.ctime(stats.st_mtime),
    }


@mcp.tool(tools)
def search_files(keyword: str, path: str = ".") -> dict:
    """Search for files by name containing a given keyword."""
    target = _safe_path(path)
    matches = []
    for root, dirs, files in os.walk(target):
        for f in files:
            if keyword.lower() in f.lower():
                matches.append(os.path.relpath(os.path.join(root, f), BASE_DIR))
    return {"matches": matches}


@mcp.tool(tools)
def search_text(keyword: str, path: str = ".") -> dict:
    """Search for text inside files, returning line matches."""
    target = _safe_path(path)
    matches = []
    for root, dirs, files in os.walk(target):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    for i, line in enumerate(fh, start=1):
                        if keyword.lower() in line.lower():
                            matches.append({
                                "file": os.path.relpath(file_path, BASE_DIR),
                                "line_number": i,
                                "line": line.strip()
                            })
            except Exception:
                continue
    return {"matches": matches}


@mcp.tool(tools)
def make_directory(path: str) -> dict:
    """Create a new directory inside the sandbox."""
    target = _safe_path(path)
    if os.path.exists(target):
        return {"error": f"Directory '{path}' already exists."}
    os.makedirs(target, exist_ok=True)
    return {"status": f"Directory '{path}' created successfully."}


@mcp.tool(tools)
def list_directories(path: str = ".") -> dict:
    """List all directories in the given path inside the sandbox."""
    target = _safe_path(path)
    return {"directories": [d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))]}


@mcp.tool(tools)
def delete_directory(path: str) -> dict:
    """Delete a directory (and its contents) inside the sandbox."""
    target = _safe_path(path)
    if not os.path.exists(target):
        return {"error": f"Directory '{path}' does not exist."}
    if not os.path.isdir(target):
        return {"error": f"'{path}' is not a directory."}
    shutil.rmtree(target)
    return {"status": f"Directory '{path}' deleted successfully."}
