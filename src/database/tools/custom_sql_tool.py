#!/usr/bin/env python3
"""
Custom SQL Tool Module
Provides a custom SQL database tool that uses cleaned SQL queries
to prevent markdown syntax errors during execution.
"""

import re
from typing import Any, Dict, Optional, List
from langchain_core.tools import BaseTool
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import ListSQLDatabaseTool, InfoSQLDatabaseTool
from pydantic import Field


class CustomQuerySQLDatabaseTool(BaseTool):
    """Custom tool for querying a SQL database with cleaned SQL queries."""
    
    name: str = "sql_db_query"
    description: str = """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    
    db: SQLDatabase = Field(exclude=True)
    
    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True
    
    def _clean_sql_query(self, sql: str) -> str:
        """Clean SQL query by removing markdown artifacts and formatting issues"""
        # Remove any markdown code block markers
        sql = re.sub(r'^```(?:sql|SQL)?\s*', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'```\s*$', '', sql, flags=re.MULTILINE)
        
        # Remove any backticks that might be left
        sql = sql.replace('`', '')
        
        # Remove extra whitespace and normalize line endings
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # Ensure the query ends with a semicolon if it doesn't already
        if sql and not sql.endswith(';'):
            sql += ';'
            
        return sql
    
    def _run(
        self,
        query: str,
        run_manager: Optional[Any] = None,
    ) -> str:
        """Execute the query, return the results or an error message."""
        try:
            # Clean the SQL query before execution
            cleaned_query = self._clean_sql_query(query)
            print(f"🧹 Cleaned SQL: {cleaned_query}")
            
            # Execute the cleaned query
            result = self.db.run(cleaned_query)
            return result
        except Exception as e:
            return f"Error: {e}"
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[Any] = None,
    ) -> str:
        """Execute the query asynchronously, return the results or an error message."""
        return self._run(query, run_manager)


class SemanticListSQLDatabaseTool(BaseTool):
    """Custom tool for listing database tables with semantic filtering."""

    name: str = "sql_db_list_tables"
    description: str = """
    Input is an empty string, output is a comma-separated list of tables in the database.
    This tool uses semantic filtering to show only the most relevant tables for the current query context.
    """

    db: SQLDatabase = Field(exclude=True)
    prompt_manager: Any = Field(exclude=True, default=None)
    current_question: str = Field(default="", exclude=True)

    def _run(self, tool_input: str = "") -> str:
        """Get list of available database tables with semantic filtering."""
        try:
            # Get all available tables
            all_tables = self.db.get_usable_table_names()

            # Apply semantic filtering if available and we have a current question
            if (self.prompt_manager and
                hasattr(self.prompt_manager, 'semantic_table_selector') and
                self.prompt_manager.semantic_table_selector and
                self.current_question):

                try:
                    # Use semantic selection to filter tables
                    filtered_tables = self.prompt_manager.get_optimized_table_list(
                        question=self.current_question,
                        available_tables=all_tables
                    )

                    if filtered_tables and len(filtered_tables) < len(all_tables):
                        print(f"🧠 Semantic filtering: showing {len(filtered_tables)} most relevant tables (from {len(all_tables)} total)")
                        return ", ".join(filtered_tables)

                except Exception as e:
                    print(f"⚠️ Semantic filtering failed: {e}, showing all tables")

            # Fallback: return all tables (or first 20 for very large databases)
            if len(all_tables) > 20:
                print(f"📊 Showing first 20 tables from {len(all_tables)} total")
                return ", ".join(all_tables[:20])
            else:
                return ", ".join(all_tables)

        except Exception as e:
            return f"Error retrieving tables: {str(e)}"

    def update_question_context(self, question: str):
        """Update the current question context for semantic filtering."""
        self.current_question = question


def create_custom_sql_toolkit(db: SQLDatabase, llm: Any, prompt_manager: Any = None, 
                             enable_enhanced_security: bool = True, 
                             security_monitor: Any = None,
                             enable_error_recovery: bool = True) -> list:
    """
    Create a custom SQL toolkit with semantic table filtering, enhanced security, and error recovery.
    
    Args:
        db: SQLDatabase instance
        llm: Language model instance
        prompt_manager: PromptManager for semantic filtering (optional)
        enable_enhanced_security: Whether to use enhanced security features
        security_monitor: SecurityMonitor instance for logging (optional)
        enable_error_recovery: Whether to use error recovery features
    """
    from langchain_community.agent_toolkits.sql.toolkit import (
        InfoSQLDatabaseTool,
        QuerySQLCheckerTool,
    )

    # Choose query tool based on feature settings
    if enable_error_recovery and enable_enhanced_security:
        try:
            from .enhanced_sql_tool import EnhancedUniversalSQLTool
            query_tool = EnhancedUniversalSQLTool(db=db, security_monitor=security_monitor)
            print("🚀 Using enhanced SQL tool with security and error recovery")
        except ImportError:
            print("⚠️ Enhanced SQL tool not available, falling back to security-only tool")
            try:
                from .secure_sql_tool import SecureUniversalSQLTool
                query_tool = SecureUniversalSQLTool(db=db, security_monitor=security_monitor)
                print("🛡️ Using enhanced security SQL tool")
            except ImportError:
                print("⚠️ Security tool not available, using standard tool")
                query_tool = CustomQuerySQLDatabaseTool(db=db)
    elif enable_enhanced_security:
        try:
            from .secure_sql_tool import SecureUniversalSQLTool
            query_tool = SecureUniversalSQLTool(db=db, security_monitor=security_monitor)
            print("🛡️ Using enhanced security SQL tool")
        except ImportError:
            print("⚠️ Enhanced security tool not available, using standard tool")
            query_tool = CustomQuerySQLDatabaseTool(db=db)
    else:
        query_tool = CustomQuerySQLDatabaseTool(db=db)
        print("📊 Using standard SQL tool (enhancements disabled)")

    # Use semantic list tool if prompt_manager is available, otherwise use standard tool
    if prompt_manager:
        list_tool = SemanticListSQLDatabaseTool(db=db, prompt_manager=prompt_manager)
        print("🧠 Using semantic table filtering for sql_db_list_tables tool")
    else:
        from langchain_community.agent_toolkits.sql.toolkit import ListSQLDatabaseTool
        list_tool = ListSQLDatabaseTool(db=db)
        print("📊 Using standard table listing (no semantic filtering)")

    tools = [
        query_tool,
        InfoSQLDatabaseTool(db=db),
        list_tool,
        QuerySQLCheckerTool(db=db, llm=llm),
    ]

    return tools


def create_enhanced_sql_toolkit(db: SQLDatabase, llm: Any, prompt_manager: Any = None,
                              security_monitor: Any = None, user_context: Dict = None,
                              enable_error_recovery: bool = True) -> list:
    """
    Create enhanced SQL toolkit with full security and error recovery features.
    
    This is a convenience function that creates a toolkit with all enhanced features enabled.
    """
    return create_custom_sql_toolkit(
        db=db,
        llm=llm,
        prompt_manager=prompt_manager,
        enable_enhanced_security=True,
        security_monitor=security_monitor,
        enable_error_recovery=enable_error_recovery
    )


