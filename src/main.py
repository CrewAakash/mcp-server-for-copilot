"""Copilot Studio Agent MCP Server"""

import logging
import sys
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from cps_connector import CopilotConnector
from mcp_server_types import ToolSuccessResponse, ToolErrorResponse, ToolResponse

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_cps_server")

def initialize_server() -> bool:
    """Initialize the Copilot Studio Agent.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        return CopilotConnector.initialize()
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
    query: str = Field(description="Query to the tool"),
    conversation_id: Optional[str] = Field(
        description="The conversation ID returned from previous response for continuing the conversation",
        default=None,
    ),
    watermark: Optional[str] = Field(
        description="The watermark returned from previous response for tracking conversation state. Watermark is used to query new messages in the conversation.",
        default=None,
    ),
) -> ToolResponse:
    """
    Send a query to the agent.
    Always use conversation_id and watermark from previous responses when available.
    
    Returns:
        ToolResponse: Response containing success/error status, message, 
        conversation_id, and watermark for continued conversation.
    """
    if not server_initialized:
        return ToolErrorResponse(
            status="error",
            message="Error: Copilot Studio agent is not initialized. Check server logs for details.",
            conversation_id=None,
            watermark=None,
        )

    try:
        # Query the agent and pass conversation context parameters
        response = await CopilotConnector.query_agent(query, conversation_id, watermark)

        # Return formatted response with conversation tracking info
        return ToolSuccessResponse(
            status="success",
            message=response["message"],
            conversation_id=response["conversation_id"],
            watermark=response["watermark"],
        )
    except Exception as e:
        return ToolErrorResponse(
            status="error",
            message=f"Error querying Copilot Studio agent: {str(e)}",
            conversation_id=None,
            watermark=None,
        )


if __name__ == "__main__":
    status = (
        "successfully initialized" if server_initialized else "initialization failed"
    )
    print(
        f"\n{'=' * 50}\nCopilot Studio Agents MCP Server {status}\nStarting server...\n{'=' * 50}\n"
    )
    mcp.run()
