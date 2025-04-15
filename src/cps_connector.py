import os
import logging
from typing import Optional, Tuple, Dict, Any, TypedDict, Union, Literal
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
                id="copilot-studio-agent",
                name="copilot-studio-agent",
                description="Copilot Studio agent via DirectLine API",
                directline_client=cls.directline_client,
            )
            
            cls.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Copilot Studio client: {str(e)}")
            return False
    
    @classmethod
    async def query_agent(
        cls, query: str, conversation_id: Optional[str] = None, watermark: Optional[str] = None
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

# For backward compatibility, maintain the global functions but implement via the class
directline_client = CopilotConnector.directline_client
copilot_agent = CopilotConnector.copilot_agent

def initialize_server() -> bool:
    """Initialize the Copilot Studio Agent (now delegates to CopilotConnector).
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    return CopilotConnector.initialize()

async def query_copilot_agent(
    query: str, conversation_id: Optional[str] = None, watermark: Optional[str] = None
) -> AgentResponse:
    """Query the Copilot Studio agent (now delegates to CopilotConnector).

    Args:
        query: The message to send to the agent
        conversation_id: Optional ID to continue an existing conversation
        watermark: Optional watermark to track conversation state

    Returns:
        AgentResponse containing the response text, conversation_id, and watermark
    """
    return await CopilotConnector.query_agent(query, conversation_id, watermark)
