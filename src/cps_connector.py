import os
import logging
from typing import Optional
from copilot_studio.copilot_agent import CopilotAgent
from copilot_studio.directline_client import DirectLineClient

logger = logging.getLogger("cps_connector")

def initialize_server() -> tuple[bool, DirectLineClient | None, CopilotAgent | None]:
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

        return True, directline_client, copilot_agent
    except Exception as e:
        logger.error(f"Failed to initialize Copilot Studio client: {str(e)}")
        return False
    

async def query_copilot_agent(
    query: str, conversation_id: Optional[str] = None, watermark: Optional[str] = None
) -> dict:
    """Query the Copilot Studio agent and get the response.

    Args:
        query: The message to send to the agent
        conversation_id: Optional ID to continue an existing conversation
        watermark: Optional watermark to track conversation state

    Returns:
        Dictionary containing the response text, conversation_id, and watermark
    """
    global copilot_agent

    if not copilot_agent:
        logger.error("Copilot agent is not initialized")
        return {
            "message": "Error: Copilot agent is not initialized",
            "conversation_id": None,
            "watermark": None,
        }

    try:
        # Query the agent and get the response
        response = await copilot_agent.query(
            message=query,
            conversation_id=conversation_id,
            watermark=watermark,
        )

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

        # Return full response with conversation tracking info
        return {
            "message": result.strip(),
            "conversation_id": response["conversation_id"],
            "watermark": response["watermark"],
        }
    except Exception as e:
        logger.error(f"Copilot agent query failed: {str(e)}")
        raise
