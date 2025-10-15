# client_runner/client.py

import asyncio
import httpx
from contextlib import asynccontextmanager

# Configuration
LOCAL_SERVER_URL = "http://localhost:8000/sse"  # FastMCP uses SSE transport
# Alternative: If using stdio transport, you'd launch the server as a subprocess

@asynccontextmanager
async def create_client():
    """Create an MCP client connected to the server."""
    async with httpx.AsyncClient() as http_client:
        from fastmcp import Client
        # Connect using FastMCP's built-in SSE client
        async with Client(LOCAL_SERVER_URL) as client:
            yield client

async def main():
    """Connects to the MCP server and uses its tools."""
    print(f"Connecting to MCP server at {LOCAL_SERVER_URL}...")
    
    try:
        async with create_client() as client:
            print("✅ Connection successful!")
            
            # List available tools
            print("\nFetching available tools...")
            tools = await client.list_tools()
            print(f"Available tools: {len(tools)}")
            # for tool in tools[:5]:  # Show first 5
            #     print(f"  - {tool.name}")
            
            # Call a specific tool
            # print("\nCalling tool 'FS: list_files'...")
            # result = await client.call_tool("FS: delete_file", {"path": "."})
            # print("\nResult from server:")
            # print(result)

    except httpx.ConnectError as e:
        print(f"\n❌ Connection Error: The server refused to connect.")
        print("   Please make sure the server is running with:")
        print("   uv run python -m mcp_server.main")
        print(f"   Details: {e}")

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())