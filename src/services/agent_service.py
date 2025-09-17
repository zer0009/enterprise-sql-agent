#!/usr/bin/env python3
"""
Agent Service for managing UniversalSQLAgent instances
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator, Any
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import from new structure first, fallback to legacy
from ..agents.sql_agent import UniversalSQLAgent

from ..database.connection import build_connection_string

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing SQL agent instances"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # Can hold UniversalSQLAgent instances
        self.agent_last_used: Dict[str, datetime] = {}
        self.default_agent: Optional[Any] = None
    
    async def initialize_default_agent(self) -> bool:
        """Initialize a default agent for system checks with startup optimization"""
        try:
            start_time = time.time()
            logger.info(f"🚀 Initializing default Universal agent...")

            # Use UniversalSQLAgent
            self.default_agent = UniversalSQLAgent()

            # Setup database (UniversalSQLAgent)
            if not await self.default_agent.setup_database():
                    logger.warning("Default agent database setup failed")
                    return False

            # Setup LLM
            if not self.default_agent.setup_llm():
                logger.warning("Default agent LLM setup failed")
                return False

            # Setup agent
            if not self.default_agent.setup_agent():
                logger.warning("Default agent setup failed")
                return False

            elapsed_time = time.time() - start_time
            logger.info(f"✅ Default agent initialized successfully in {elapsed_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize default agent: {e}")
            return False

    async def get_agent(self, session_id: str = "default") -> Optional[Any]:
        """Get an agent instance for a session"""
        try:
            # Return default agent if available
            if self.default_agent:
                return self.default_agent
            
            # Create new agent if needed
            if session_id not in self.agents:
                logger.info(f"Creating new agent for session: {session_id}")
                agent = UniversalSQLAgent()
                
                # Setup agent components
                if not await agent.setup_database():
                    logger.error(f"Failed to setup database for session {session_id}")
                    return None
                
                if not agent.setup_llm():
                    logger.error(f"Failed to setup LLM for session {session_id}")
                    return None
                
                if not agent.setup_agent():
                    logger.error(f"Failed to setup agent for session {session_id}")
                    return None
                
                self.agents[session_id] = agent
                self.agent_last_used[session_id] = datetime.now()
            
            return self.agents[session_id]
            
        except Exception as e:
            logger.error(f"Failed to get agent for session {session_id}: {e}")
            return None

    async def process_question(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """Process a question using an agent"""
        try:
            agent = await self.get_agent(session_id)
            if not agent:
                return {
                    "status": "error",
                    "content": "Failed to initialize agent",
                    "session_id": session_id
                }
            
            # Update last used time
            self.agent_last_used[session_id] = datetime.now()
            
            # Process the question
            result = await agent.process_question(question)
            result["session_id"] = session_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing question for session {session_id}: {e}")
            return {
                "status": "error",
                "content": f"Error processing question: {str(e)}",
                "session_id": session_id
            }

    async def cleanup_old_agents(self, max_age_hours: int = 24):
        """Cleanup old agent instances"""
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, last_used in self.agent_last_used.items():
                age_hours = (current_time - last_used).total_seconds() / 3600
                if age_hours > max_age_hours:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                if session_id in self.agents:
                    agent = self.agents[session_id]
                    if hasattr(agent, 'close'):
                        await agent.close()
                    del self.agents[session_id]
                    del self.agent_last_used[session_id]
                    logger.info(f"Cleaned up old agent for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error during agent cleanup: {e}")

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about agent instances"""
        return {
            "total_agents": len(self.agents),
            "default_agent_available": self.default_agent is not None,
            "sessions": list(self.agents.keys()),
            "last_used_times": {
                session_id: last_used.isoformat() 
                for session_id, last_used in self.agent_last_used.items()
            }
        }

    async def close_all_agents(self):
        """Close all agent instances"""
        try:
            # Close default agent
            if self.default_agent and hasattr(self.default_agent, 'close'):
                await self.default_agent.close()
            
            # Close session agents
            for session_id, agent in self.agents.items():
                if hasattr(agent, 'close'):
                    await agent.close()
            
            self.agents.clear()
            self.agent_last_used.clear()
            self.default_agent = None
            
            logger.info("All agents closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing agents: {e}")





