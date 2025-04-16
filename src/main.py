"""Copilot Studio Agent MCP Server"""

import json
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from cps_connector import CopilotConnector
from mcp_server_types import (
    AgentDefinition,
    ToolErrorResponse,
    ToolResponse,
    ToolSuccessResponse,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_cps_server")


def load_agent_definition() -> AgentDefinition:
    """Load agent definition from JSON file.

    Returns:
        AgentDefinition: Object containing agent name and description
    """
    default_definition = AgentDefinition(
        name="Copilot Agent",
        description="An agent that runs in the Microsoft copilot studio.",
    )

    try:
        # Look for agent_definition.json in the root directory
        agent_def_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "agent_definition.json"
        )
        if os.path.exists(agent_def_path):
            with open(agent_def_path, "r") as f:
                data = json.load(f)
                return AgentDefinition(
                    name=data["name"], description=data["description"]
                )
        else:
            logger.warning("agent_definition.json not found, using default definition")
            return default_definition
    except Exception as e:
        logger.error(f"Failed to load agent definition: {str(e)}")
        return default_definition


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
agent = load_agent_definition()

# Use agent name and description for the MCP server
mcp = FastMCP(
    agent.name.lower().replace(" ", "-"),
    description=agent.description,
    dependencies=["python-dotenv", "aiohttp", "typing-extensions"],
)


@mcp.tool()
async def query_agent(
    query: str = Field(description=f"Query to send to the {agent.name}"),
    conversation_id: Optional[str] = Field(
        description="The conversation ID returned from previous response for continuing the conversation",
        default=None,
    ),
    watermark: Optional[str] = Field(
        description="The watermark returned from previous response for tracking conversation state. Watermark is used to query new messages in the conversation.",
        default=None,
    ),
) -> ToolResponse:
    f"""
    Send a query to the {agent.name}.
    {agent.description}
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
