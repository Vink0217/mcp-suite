import subprocess
import tempfile
import os
from mcp.server.fastmcp import FastMCP as MCP
mcp = MCP("Development Tools")

BASE_DIR = os.path.abspath("./workspace")
os.makedirs(BASE_DIR, exist_ok=True)

tools = []


def _run_cmd(cmd: list | str, timeout: int = 10, shell: bool = False) -> dict:
    """Helper to run subprocess commands safely inside workspace."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=BASE_DIR
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command {cmd} timed out after {timeout} seconds."}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools, structured_output={"stdout": str, "stderr": str, "returncode": int, "error": str})
def run_python(code: str, timeout: int = 5) -> dict:
    """Run a Python code snippet safely in a subprocess."""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", dir=BASE_DIR, delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        return _run_cmd(["python", tmp_path], timeout)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(tools, structured_output={"stdout": str, "stderr": str, "returncode": int, "error": str})
def run_shell(command: str, timeout: int = 5) -> dict:
    """Run a limited shell command in the workspace (ls, echo, pwd, cat only)."""
    allowed = ["ls", "echo", "pwd", "cat"]
    cmd_name = command.split()[0]
    if cmd_name not in allowed:
        return {"error": f"Command '{cmd_name}' not allowed."}
    return _run_cmd(command, timeout, shell=True)


@mcp.tool(tools, structured_output={"stdout": str, "stderr": str, "returncode": int, "error": str})
def run_tests(timeout: int = 10) -> dict:
    """Run pytest in the workspace and return results."""
    return _run_cmd(["pytest", "-q"], timeout)


@mcp.tool(tools, structured_output={"stdout": str, "stderr": str, "returncode": int, "error": str})
def lint_code(path: str = ".") -> dict:
    """Lint Python files with flake8 (requires flake8 installed)."""
    return _run_cmd(["flake8", path])


@mcp.tool(tools, structured_output={"stdout": str, "stderr": str, "returncode": int, "error": str})
def format_code(path: str = ".") -> dict:
    """Format Python files with black (requires black installed)."""
    return _run_cmd(["black", path])


@mcp.tool(tools, structured_output={"stdout": str, "stderr": str, "returncode": int, "error": str})
def install_package(package: str) -> dict:
    """Install a Python package into workspace using pip."""
    return _run_cmd(["pip", "install", "--target", BASE_DIR, package])
