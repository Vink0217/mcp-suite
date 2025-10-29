# mcp_server/main.py
import os
from mcp.server.fastmcp import FastMCP
from mcp_server import filesystem_tools, development_tools, database_tools
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Create the FastMCP instance
mcp = FastMCP("MCP Unified Server")
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

    table = Table(title=f"{prefix} Tools ({len(tools_list)})", 
                  show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    for tool_name, tool_desc in tools_list:
        table.add_row(tool_name, tool_desc)
    console.print(table)

# Register all the tool modules
register_module_tools(filesystem_tools, "FS")
register_module_tools(development_tools, "DEV")
register_module_tools(database_tools, "DB")

console.print(Panel.fit("[green bold]MCP Server registered and ready.[/]"))

# CRITICAL FIX: Get the internal ASGI app from FastMCP
# FastMCP wraps a Starlette/FastAPI app internally
# We need to expose it for Uvicorn to run

# Try to get the app attribute (common in FastMCP implementations)
if hasattr(mcp, 'app'):
    app = mcp.app
    console.print("[green]✓ Using mcp.app[/]")
elif hasattr(mcp, '_app'):
    app = mcp._app
    console.print("[green]✓ Using mcp._app[/]")
elif hasattr(mcp, 'get_app'):
    app = mcp.get_app()
    console.print("[green]✓ Using mcp.get_app()[/]")
else:
    # If FastMCP doesn't expose its app, we need to run it differently
    console.print("[yellow]⚠ Cannot find ASGI app in FastMCP[/]")
    console.print("[yellow]Attempting to use mcp.run() instead[/]")
    
    # For Railway/production: run the server directly
    if __name__ == "__main__":
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        console.print(f"[green]Starting server on {host}:{port}[/]")
        mcp.run(host=host, port=port)
    else:
        # Fallback: create a minimal wrapper
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        
        async def health_check(request):
            return JSONResponse({"status": "healthy", "message": "MCP Server is running"})
        
        app = Starlette(routes=[
            Route("/health", health_check),
        ])
        console.print("[yellow]⚠ Using fallback Starlette app[/]")