"""Type definitions for MCP server."""

from typing import Optional, TypedDict, Literal, Union

# Response type definitions for the CopilotConnector
class AgentResponse(TypedDict):
    """Type definition for agent response."""
    message: str
    conversation_id: Optional[str]
    watermark: Optional[str]

# Response type definitions for the MCP tool
class ToolSuccessResponse(TypedDict):
    """Type definition for a successful tool response."""
    status: Literal["success"]
    message: str
    conversation_id: str
    watermark: str

class ToolErrorResponse(TypedDict):
    """Type definition for an error tool response."""
    status: Literal["error"]
    message: str
    conversation_id: None
    watermark: None

# Combined type for tool responses
ToolResponse = Union[ToolSuccessResponse, ToolErrorResponse]
