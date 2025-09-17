"""Database Connection Module
Provides database connection pool access for the API routes
"""

import logging
from typing import Optional, Dict, Any
import asyncpg
from langchain_community.utilities import SQLDatabase

logger = logging.getLogger(__name__)

# Global database manager instance
_db_manager = None

def get_db_manager():
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        from src.database.schema import DatabaseManager
        _db_manager = DatabaseManager()
    return _db_manager

async def get_db_pool() -> Optional[asyncpg.Pool]:
    """Get database connection pool"""
    try:
        db_manager = get_db_manager()
        if db_manager.pool is None:
            # Initialize the pool if it doesn't exist
            await db_manager.initialize()
        return db_manager.pool
    except Exception as e:
        logger.error(f"Failed to get database pool: {e}")
        return None

async def initialize_database():
    """Initialize database connection"""
    try:
        db_manager = get_db_manager()
        success = await db_manager.initialize()
        if success:
            logger.info("✅ Database connection established")
        else:
            logger.warning("⚠️ Database connection failed")
        return success
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

async def close_database():
    """Close database connection"""
    try:
        db_manager = get_db_manager()
        await db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Database close error: {e}")

def get_sql_database(connection_string: Optional[str] = None) -> Optional[SQLDatabase]:
    """Get or create SQLDatabase instance"""
    try:
        if connection_string:
            sql_database = SQLDatabase.from_uri(connection_string)
            logger.info("✅ SQLDatabase instance created")
            return sql_database
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to create SQLDatabase: {e}")
        return None

def build_connection_string() -> str:
    """Build database connection string from environment or config"""
    import os
    
    # Try environment variables first
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'universal_sql_agent')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'password')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

