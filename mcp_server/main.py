# mcp_server/main.py
import os
from mcp.server.fastmcp import FastMCP
from mcp_server import filesystem_tools, development_tools, database_tools
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- Read Configuration from Environment Variables ---
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# --- Create and Configure the Server ---
# Pass the host and port to the FastMCP constructor.
mcp = FastMCP("MCP Unified Server", host=HOST, port=PORT)
console = Console()

def register_module_tools(module, prefix: str):
    """Register all tools with the mcp instance."""
    tools_list = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        func = getattr(module, name)
        if callable(func) and func.__module__ == module.__name__:
            tool_name = f"{prefix}: {name}"
            tool_desc = func.__doc__.strip() if func.__doc__ else ""
            mcp.tool(name=tool_name, description=tool_desc)(func)
            tools_list.append((tool_name, tool_desc))
            
    table = Table(title=f"{prefix} Tools ({len(tools_list)})", show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    for tool_name, tool_desc in tools_list:
        table.add_row(tool_name, tool_desc)
    console.print(table)

# Register all the tool modules
register_module_tools(filesystem_tools, "FS")
register_module_tools(development_tools, "DEV")
register_module_tools(database_tools, "DB")

# --- Run the Server Using Its Own Method ---
if __name__ == "__main__":
    console.print(Panel.fit(f"[green bold]Starting MCP Server on {HOST}:{PORT}...[/]"))
    # Use SSE transport but let FastMCP use the host/port from constructor
    mcp.run(transport="sse")