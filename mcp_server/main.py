# mcp_server/main.py
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
            # Register tools with our mcp instance
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

console.print(Panel.fit("[green bold]MCP Server is ready to be served by Uvicorn.[/]"))

# FastMCP internally uses FastAPI/Starlette
# Access the underlying ASGI application
# Try different possible attributes
try:
    if hasattr(mcp, 'app'):
        app = mcp.app
    elif hasattr(mcp, '_app'):
        app = mcp._app
    elif hasattr(mcp, 'get_asgi_app'):
        app = mcp.get_asgi_app()
    else:
        # Create a simple wrapper if needed
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.post("/")
        async def handle_mcp(request: dict):
            # This is a fallback - you may need to adjust based on MCP protocol
            return {"error": "Direct ASGI access not available"}
        
        console.print("[yellow]Warning: Using fallback ASGI wrapper[/]")
except Exception as e:
    console.print(f"[red]Error creating ASGI app: {e}[/]")
    # Fallback: create a basic FastAPI app
    from fastapi import FastAPI
    app = FastAPI()
    console.print("[yellow]Using basic FastAPI fallback[/]")

app = mcp._app if hasattr(mcp, '_app') else mcp.app if hasattr(mcp, 'app') else mcp