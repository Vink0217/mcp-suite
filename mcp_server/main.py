# mcp_server/main.py
import os
from fastapi import FastAPI, Request, HTTPException
# Correct import path
from fastmcp import FastMCP
from mcp_server import filesystem_tools, development_tools, database_tools
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import logging
import json # Ensure json is imported

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration (No Change needed here) ---
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

# --- Build the MCP Engine ---
mcp_engine = FastMCP("MCP Unified Server")
console = Console()

# --- Tool Registration ---
def register_module_tools(module, prefix: str):
    tools_list = []
    registered_count = 0
    for name in dir(module):
        if name.startswith("_"):
            continue
        func = getattr(module, name)
        if callable(func) and hasattr(func, '__module__') and func.__module__ == module.__name__:
            tool_name = f"{prefix}: {name}"
            tool_desc = func.__doc__.strip() if func.__doc__ else "No description available."
            try:
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
except Exception as e:
    logger.error(f"An unexpected error occurred during tool registration: {e}")

# --- Build the FastAPI "Front Door" ---
# This IS the main app Uvicorn runs.
app = FastAPI(title="MCP Server with HTTP Bridge")
logger.info("FastAPI app created.")

@app.post("/call_tool")
async def handle_call_tool(request: Request):
    """ HTTP endpoint for external services to call MCP tools. """
    logger.info(f"Received request at /call_tool from {request.client.host}")
    try:
        body = await request.json()
        tool_name = body.get("name")
        tool_params = body.get("params", {})

        if not tool_name:
             logger.error("Request missing 'name' field.")
             raise HTTPException(status_code=400, detail="Missing 'name' field")

        logger.info(f"Processing tool call: {tool_name} with params: {tool_params}")

        if tool_name not in mcp_engine.tools:
            logger.error(f"Tool '{tool_name}' not found.")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        tool_definition = mcp_engine.tools[tool_name]
        tool_function = tool_definition.function

        result = tool_function(**tool_params)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return result

    except json.JSONDecodeError:
        logger.error("Received invalid JSON in /call_tool request.")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException as http_exc:
        logger.warning(f"HTTP exception during /call_tool: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error executing tool '{tool_name or 'unknown'}' via /call_tool")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Health Check Endpoint AT THE ROOT ---
@app.get("/")
async def root_health_check():
    """Simple root endpoint for Railway health check."""
    logger.info("Received GET request at / (health check)")
    return {"status": "ok", "message": "MCP Server is running"}

# --- Mount the MCP Engine (Optional - keep commented out for now) ---
# If you need your local client_runner to work via MCP protocol later,
# you can uncomment this and adjust the path. For now, keep it off.
# app.mount("/mcp", mcp_engine)

console.print(Panel.fit("[green bold]MCP Server with FastAPI front door is ready.[/]"))
logger.info("Server setup complete, ready for Uvicorn.")

# DO NOT add the complex try/except block or mcp.run() here.
# Uvicorn runs the 'app' object defined above via the Dockerfile CMD.