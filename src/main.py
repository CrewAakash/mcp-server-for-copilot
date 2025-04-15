"""Copilot Studio Agent MCP Server"""

import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from copilot_studio.copilot_agent import CopilotAgent
from copilot_studio.directline_client import DirectLineClient
import json
from cps_connector import initialize_server as cps_initialize_server
from cps_connector import query_copilot_agent as cps_query_copilot_agent

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_cps_server")

# Global variables for DirectLine Client and Copilot Agent
directline_client = None
copilot_agent = None


def initialize_server():
    """Initialize the Copilot Studio Agent."""
    global directline_client, copilot_agent

    try:
        status, directline_client, copilot_agent = cps_initialize_server()
        return status
    except Exception as e:
        logger.error(f"Failed to initialize Copilot Studio client: {str(e)}")
        return False

# Initialize MCP and server
load_dotenv()

server_initialized = initialize_server()

mcp = FastMCP(
    "copilot-studio", 
    description="MCP server for Copilot Studio agent integration via DirectLine API",
    dependencies=["python-dotenv", "aiohttp", "typing-extensions"],
)

@mcp.tool()
async def query_agent(
    query: str = Field(description="The message to send to the Copilot Studio agent"),
    conversation_id: Optional[str] = Field(
        description="The conversation ID returned from previous response for continuing the conversation",
        default=None,
    ),
    watermark: Optional[str] = Field(
        description="The watermark returned from previous response for tracking conversation state. Watermark is used to query new messages in the conversation.",
        default=None,
    ),
    ctx: Context = None,
) -> dict:
    """
    Send a query to the Copilot Studio agent.
    Always use conversation_id and watermark from previous responses when available.
    """
    if not server_initialized:
        return {
            "status": "error",
            "message": "Error: Copilot Studio agent is not initialized. Check server logs for details.",
            "conversation_id": None,
            "watermark": None,
        }

    try:
        # Query the agent and pass conversation context parameters
        response = await cps_query_copilot_agent(query, conversation_id, watermark)

        # Return formatted response with conversation tracking info
        return {
            "status": "success",
            "message": response["message"],
            "conversation_id": response["conversation_id"],
            "watermark": response["watermark"],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error querying Copilot Studio agent: {str(e)}",
            "conversation_id": None,
            "watermark": None,
        }


if __name__ == "__main__":
    status = (
        "successfully initialized" if server_initialized else "initialization failed"
    )
    print(
        f"\n{'=' * 50}\nCopilot Studio Agents MCP Server {status}\nStarting server...\n{'=' * 50}\n"
    )
    mcp.run(transport="sse", port=3000)
