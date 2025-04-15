"""CopilotAgent class for Microsoft Copilot Studio integration."""

import asyncio
import logging
from typing import Any, Dict, Optional

from copilot_studio.directline_client import DirectLineClient

logger = logging.getLogger(__name__)


class CopilotAgent:
    """
    A simplified agent that communicates with a Microsoft Copilot Studio bot via the Direct Line API.
    It serializes user inputs into Direct Line payloads, handles asynchronous response polling,
    and processes the bot's responses without any Semantic Kernel dependencies.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        directline_client: DirectLineClient,
    ) -> None:
        """
        Initialize the CopilotAgent.

        Args:
            id: A unique identifier for the agent
            name: A display name for the agent
            description: A description of the agent
            directline_client: The DirectLine client for API communication
        """
        self.id = id
        self.name = name
        self.description = description
        self.directline_client = directline_client

    async def start_conversation(self) -> str:
        """
        Start a new conversation with the Copilot Studio agent.

        Returns:
            The conversation ID from the DirectLine API
        """
        if not self.directline_client:
            raise Exception("DirectLine client is not initialized")

        return await self.directline_client.start_conversation()

    def build_payload(
        self,
        message: str,
        message_data: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the message payload for the DirectLine Bot.

        Args:
            message: The text message to send
            message_data: Optional dict that will be sent as the "value" field in the payload
                for adaptive card responses
            conversation_id: The conversation ID

        Returns:
            A dictionary representing the payload to be sent to the DirectLine Bot
        """
        payload = {
            "type": "message",
            "from": {"id": "user"},
        }

        if message_data and "adaptive_card_response" in message_data:
            payload["value"] = message_data["adaptive_card_response"]
        else:
            payload["text"] = message

        if conversation_id:
            payload["conversationId"] = conversation_id

        return payload

    async def post_message_and_poll(
        self,
        message: str,
        conversation_id: str,
        watermark: Optional[str] = None,
        message_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Post a message to the conversation and poll for the response.

        Args:
            message: The text message to send
            conversation_id: The conversation ID
            watermark: The watermark for tracking conversation state
            message_data: Optional dict for adaptive card responses

        Returns:
            A tuple containing (response_data, new_watermark)
        """
        if not self.directline_client:
            raise Exception("DirectLine client is not initialized")

        # Build the payload
        payload = self.build_payload(message, message_data, conversation_id)

        # Post the message
        await self.directline_client.post_activity(conversation_id, payload)

        # Poll for new activities using watermark until we get a bot response
        finished = False
        collected_data = None
        current_watermark = watermark

        while not finished:
            data = await self.directline_client.get_activities(
                conversation_id, current_watermark
            )

            # Update watermark if present
            if "watermark" in data:
                current_watermark = data["watermark"]

            activities = data.get("activities", [])

            # Check for either DynamicPlanFinished event or message from bot
            if any(
                (
                    activity.get("type") == "event"
                    and activity.get("name") == "DynamicPlanFinished"
                )
                or (
                    activity.get("type") == "message"
                    and activity.get("from", {}).get("role") == "bot"
                )
                for activity in activities
            ):
                collected_data = data
                finished = True
                break

            await asyncio.sleep(1)

        return {"data": collected_data, "watermark": current_watermark}

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the response from DirectLine API into a structured format.

        Args:
            response_data: The raw response data from DirectLine

        Returns:
            A structured response with text, adaptive cards, and suggested actions
        """
        if not response_data or "activities" not in response_data.get("data", {}):
            raise Exception("Invalid response from DirectLine Bot")

        activities = response_data["data"]["activities"]

        result = {
            "text": "",
            "adaptive_card": None,
            "suggested_actions": [],
            "watermark": response_data["watermark"],
        }

        for activity in activities:
            # Skip non-bot messages or non-message types
            if (
                activity.get("type") != "message"
                or activity.get("from", {}).get("id") == "user"
                or activity.get("from", {}).get("role") != "bot"
            ):
                continue

            # Extract text content
            if "text" in activity:
                result["text"] = activity.get("text", "")

            # Extract suggested actions
            suggested_actions = activity.get("suggestedActions", {}).get("actions", [])
            if suggested_actions:
                result["suggested_actions"] = suggested_actions

            # Extract adaptive card if present
            attachments = activity.get("attachments", [])
            if (
                attachments
                and attachments[0].get("contentType")
                == "application/vnd.microsoft.card.adaptive"
            ):
                result["adaptive_card"] = attachments[0].get("content", {})

        return result

    async def query(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        watermark: Optional[str] = None,
        message_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Convenience method that combines conversation creation (if needed),
        sending a message, and parsing the response.

        Args:
            message: The message to send
            conversation_id: Optional existing conversation ID
            watermark: Optional watermark from previous messages
            message_data: Optional dict for adaptive card responses

        Returns:
            Parsed response from the agent
        """
        # Create a new conversation if needed
        if not conversation_id:
            conversation_id = await self.start_conversation()

        # Send the message and wait for response
        response_data = await self.post_message_and_poll(
            message, conversation_id, watermark, message_data
        )

        # Parse the response
        result = self.parse_response(response_data)

        # Add conversation ID to the result
        result["conversation_id"] = conversation_id

        return result

    async def close(self) -> None:
        """
        Clean up resources.
        """
        if self.directline_client:
            await self.directline_client.close()
