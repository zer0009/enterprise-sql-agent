#!/usr/bin/env python3
"""
Pydantic models for chat API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """Individual chat message model"""
    content: str = Field(..., description="Message content")
    type: str = Field(default="human", description="Message type: human, ai, tool, system")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")

class ChatRequest(BaseModel):
    """Chat request model for streaming endpoint"""
    messages: List[ChatMessage] = Field(..., description="List of conversation messages")
    user_role: str = Field(default="employee", description="User role for context")
    user_id: int = Field(default=1, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier for conversation context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "content": "Show me the first 10 customers",
                        "type": "human"
                    }
                ],
                "user_role": "employee",
                "user_id": 1,
                "session_id": "demo-session"
            }
        }

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall system status")
    database_connected: bool = Field(..., description="Database connection status")
    llm_configured: bool = Field(..., description="LLM configuration status")
    active_sessions: int = Field(..., description="Number of active chat sessions")
    timestamp: datetime = Field(..., description="Health check timestamp")

class ConfigResponse(BaseModel):
    """System configuration response model"""
    database_type: Optional[str] = Field(None, description="Connected database type")
    available_tables: List[str] = Field(default=[], description="List of accessible database tables")
    llm_model: Optional[str] = Field(None, description="Currently configured LLM model")
    features: Dict[str, bool] = Field(..., description="Available system features")
    error: Optional[str] = Field(None, description="Configuration error if any")

class StreamResponse(BaseModel):
    """Streaming response chunk model"""
    response: Optional[str] = Field(None, description="Response content chunk")
    error: Optional[str] = Field(None, description="Error message if any")
    status: Optional[str] = Field(None, description="Processing status")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str = Field(..., description="Session identifier")
    user_id: int = Field(..., description="User identifier")
    user_role: str = Field(..., description="User role")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    is_active: bool = Field(..., description="Whether session is currently active")

class SessionListResponse(BaseModel):
    """Response model for session list endpoint"""
    active_sessions: int = Field(..., description="Number of active sessions")
    sessions: List[SessionInfo] = Field(..., description="List of session information")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    session_id: Optional[str] = Field(None, description="Session identifier if applicable")








