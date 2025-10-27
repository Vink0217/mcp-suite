# mcp_server/main.py
import os
from fastapi import FastAPI, Request, HTTPException
from mcp.server.fastmcp import FastMCP
from mcp_server import filesystem_tools, development_tools, database_tools
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import logging # Added for better logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Step 1: Read Configuration ---
# HOST and PORT are now primarily for Uvicorn via Dockerfile,
# but we keep them here for potential direct runs or clarity.
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# --- Step 2: Build the MCP Engine ---
# This is our core tool server, NOT the main app Uvicorn runs.
mcp_engine = FastMCP("MCP Unified Server")
console = Console()

# --- Step 3: Tool Registration ---
def register_module_tools(module, prefix: str):
    """Register all tools with the mcp_engine."""
    tools_list = []
    registered_count = 0
    for name in dir(module):
        if name.startswith("_"):
            continue
        func = getattr(module, name)
        # Ensure it's a function defined *in* that module
        if callable(func) and hasattr(func, '__module__') and func.__module__ == module.__name__:
            tool_name = f"{prefix}: {name}"
            tool_desc = func.__doc__.strip() if func.__doc__ else "No description available."
            try:
                # Register tools with our engine instance
                mcp_engine.tool(name=tool_name, description=tool_desc)(func)
                tools_list.append((tool_name, tool_desc))
                registered_count += 1
            except Exception as e:
                 logger.error(f"Failed to register tool {name} from {module.__name__}: {e}")

    if registered_count > 0:
        table = Table(title=f"{prefix} Tools ({registered_count})", show_header=True, header_style="bold magenta")
        table.add_column("Tool Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        for tool_name, tool_desc in tools_list:
            table.add_row(tool_name, tool_desc)
        console.print(table)
    else:
        logger.warning(f"No tools found or registered in module: {module.__name__}")


logger.info("Registering tools...")
try:
    register_module_tools(filesystem_tools, "FS")
    register_module_tools(development_tools, "DEV")
    register_module_tools(database_tools, "DB")
    logger.info("Tool registration complete.")
except ImportError as e:
    logger.error(f"Failed to import tool modules: {e}")
    # Consider exiting if tool modules are essential
except Exception as e:
    logger.error(f"An unexpected error occurred during tool registration: {e}")


# --- Step 4: Build the FastAPI "Front Door" ---
# This is our new main app that Uvicorn will run.
app = FastAPI(title="MCP Server with HTTP Bridge")

@app.post("/call_tool")
async def handle_call_tool(request: Request):
    """
    HTTP endpoint for external services (like Vercel) to call MCP tools.
    Expects JSON: {"name": "Tool: Name", "params": {"arg1": "value1"}}
    """
    try:
        body = await request.json()
        tool_name = body.get("name")
        tool_params = body.get("params", {}) # Default to empty dict if params missing

        if not tool_name:
             logger.error("Received /call_tool request missing 'name' field.")
             raise HTTPException(status_code=400, detail="Missing 'name' field in request body")

        logger.info(f"Received HTTP request for tool: {tool_name} with params: {tool_params}")

        # Check if the tool exists in the engine's registry
        if tool_name not in mcp_engine.tools:
            logger.error(f"Tool '{tool_name}' not found in MCP engine.")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Get the actual tool function
        tool_definition = mcp_engine.tools[tool_name]
        tool_function = tool_definition.function

        # Call the tool function with the provided parameters
        # Using **tool_params unpacks the dictionary into keyword arguments
        result = tool_function(**tool_params)

        logger.info(f"Tool '{tool_name}' executed successfully.")
        return result

    except json.JSONDecodeError:
        logger.error("Received invalid JSON in /call_tool request.")
        raise HTTPException(status_code=400, detail="Invalid JSON format in request body")
    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc
    except Exception as e:
        logger.exception(f"Error executing tool '{tool_name or 'unknown'}' via /call_tool") # Log full traceback
        raise HTTPException(status_code=500, detail=f"Internal server error executing tool: {e}")

# --- Step 5: Mount the MCP Engine ---
# Mount the original MCP server (engine) at the root path.
# This allows your local MCP client (client_runner) to still connect directly via MCP protocol.
app.mount("/", mcp_engine)

console.print(Panel.fit("[green bold]MCP Server with FastAPI front door is ready.[/]"))

# The 'if __name__ == "__main__":' block is no longer needed.
# Uvicorn, run via the Dockerfile CMD, will start the 'app' object.