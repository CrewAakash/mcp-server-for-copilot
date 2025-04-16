import logging
import os
from typing import Optional, Tuple, TypedDict

from copilot_studio.copilot_agent import CopilotAgent
from copilot_studio.directline_client import DirectLineClient

logger = logging.getLogger("cps_connector")


# Define the return type for query_copilot_agent
class AgentResponse(TypedDict):
    """Type definition for agent response."""

    message: str
    conversation_id: Optional[str]
    watermark: Optional[str]


# Define the return type for initialize_server
InitServerResult = Tuple[bool, Optional[DirectLineClient], Optional[CopilotAgent]]


class CopilotConnector:
    """Class to encapsulate Copilot Studio connection and functionality."""

    # Class-level variables for DirectLine Client and Copilot Agent
    directline_client: Optional[DirectLineClient] = None
    copilot_agent: Optional[CopilotAgent] = None
    is_initialized: bool = False

    @classmethod
    def initialize(cls) -> bool:
        """Initialize the Copilot Studio Agent.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
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
            cls.directline_client = DirectLineClient(
                directline_endpoint=directline_endpoint,
                copilot_agent_secret=copilot_agent_secret,
            )

            # Create a Copilot agent instance
            cls.copilot_agent = CopilotAgent(
                directline_client=cls.directline_client,
            )

            cls.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Copilot Studio client: {str(e)}")
            return False

    @classmethod
    async def query_agent(
        cls,
        query: str,
        conversation_id: Optional[str] = None,
        watermark: Optional[str] = None,
    ) -> AgentResponse:
        """Query the Copilot Studio agent and get the response.

        Args:
            query: The message to send to the agent
            conversation_id: Optional ID to continue an existing conversation
            watermark: Optional watermark to track conversation state

        Returns:
            AgentResponse containing the response text, conversation_id, and watermark
        """
        if not cls.copilot_agent:
            logger.error("Copilot agent is not initialized")
            return {
                "message": "Error: Copilot agent is not initialized",
                "conversation_id": None,
                "watermark": None,
            }

        try:
            # Query the agent and get the response
            response = await cls.copilot_agent.query(
                message=query,
                conversation_id=conversation_id,
                watermark=watermark,
            )

            # Return full response with conversation tracking info
            return {
                "message": response["message"],
                "conversation_id": response["conversation_id"],
                "watermark": response["watermark"],
            }
        except Exception as e:
            logger.error(f"Copilot agent query failed: {str(e)}")
            raise
