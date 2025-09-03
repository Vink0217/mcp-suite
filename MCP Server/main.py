# main.py
from mcp.server.fastmcp import FastMCP
import filesystem_tools, development_tools, database_tools

mcp = FastMCP("MCP Unified Server")

def register_module_tools(module, prefix: str):
    """
    Register all functions from a module as MCP tools,
    with prefixed names and docstring descriptions.
    """
    for name in dir(module):
        if name.startswith("_"):  # skip private helpers
            continue
        func = getattr(module, name)
        if callable(func) and func.__module__ == module.__name__:
            tool_name = f"{prefix}: {name}"
            tool_desc = func.__doc__.strip() if func.__doc__ else ""
            mcp.tool(name=tool_name, description=tool_desc)(func)

# Group each toolset
register_module_tools(filesystem_tools, "FS")
register_module_tools(development_tools, "DEV")
register_module_tools(database_tools, "DB")

if __name__ == "__main__":
    mcp.run()
