"""Copilot Studio Agent MCP Server"""

import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

from copilot_studio.copilot_agent import CopilotAgent
from copilot_studio.directline_client import DirectLineClient

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("copilot_studio_mcp")

# Global variables for DirectLine client and agent
directline_client = None
copilot_agent = None
current_conversation_id = None
current_watermark = None


def initialize_server():
    """Initialize the Copilot Studio Agent."""
    global directline_client, copilot_agent

    # Load environment variables
    directline_endpoint = os.getenv("DIRECTLINE_ENDPOINT")
    copilot_agent_secret = os.getenv("COPILOT_AGENT_SECRET")

    if not directline_endpoint or not copilot_agent_secret:
        logger.error(
            "Missing required environment variables: DIRECTLINE_ENDPOINT and/or COPILOT_AGENT_SECRET"
        )
        return False

    try:
        # Initialize the DirectLine client
        directline_client = DirectLineClient(
            directline_endpoint=directline_endpoint,
            copilot_agent_secret=copilot_agent_secret,
        )

        # Create a Copilot agent instance
        copilot_agent = CopilotAgent(
            id="copilot-studio-agent",
            name="copilot-studio-agent",
            description="Copilot Studio agent via DirectLine API",
            directline_client=directline_client,
        )

        return True
    except Exception as e:
        logger.error(f"Failed to initialize Copilot Studio client: {str(e)}")
        return False


async def query_copilot_agent(query: str) -> str:
    """Query the Copilot Studio agent and get the response."""
    global copilot_agent, current_conversation_id, current_watermark

    if not copilot_agent:
        logger.error("Copilot agent is not initialized")
        return "Error: Copilot agent is not initialized"

    try:
        # Query the agent and get the response
        response = await copilot_agent.query(
            message=query,
            conversation_id=current_conversation_id,
            watermark=current_watermark,
        )

        # Update the global conversation state
        current_conversation_id = response["conversation_id"]
        current_watermark = response["watermark"]

        # Extract the content from the response
        result = response["text"]

        # Handle adaptive cards if present
        if response["adaptive_card"]:
            # You could format the adaptive card data here
            # For simplicity, we're just noting its presence
            result += "\n\n(Note: This response contains an adaptive card that can't be fully displayed in text format.)"

        # Handle suggested actions if present
        if response["suggested_actions"]:
            result += "\n\n## Suggested Actions\n"
            for action in response["suggested_actions"]:
                if "title" in action and "value" in action:
                    result += f"- {action['title']}\n"

        return result.strip()
    except Exception as e:
        logger.error(f"Copilot agent query failed: {str(e)}")
        raise


# Initialize MCP and server
load_dotenv()
server_initialized = initialize_server()
mcp = FastMCP(
    "copilot-studio",
    description="MCP server for Copilot Studio agent integration via DirectLine API",
    dependencies=["python-dotenv", "aiohttp", "typing-extensions"],
)


@mcp.tool()
async def query_agent(query: str, ctx: Context = None) -> str:
    """Send a query to the Copilot Studio agent."""
    if not server_initialized:
        return "Error: Copilot Studio agent is not initialized. Check server logs for details."

    try:
        response = await query_copilot_agent(query)
        return f"## Response from Copilot Studio Agent\n\n{response}"
    except Exception as e:
        return f"Error querying Copilot Studio agent: {str(e)}"


if __name__ == "__main__":
    status = (
        "successfully initialized" if server_initialized else "initialization failed"
    )
    print(
        f"\n{'=' * 50}\nAzure AI Agent MCP Server {status}\nStarting server...\n{'=' * 50}\n"
    )
    mcp.run()
