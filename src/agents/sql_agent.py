#!/usr/bin/env python3
"""
Main SQL Agent Class
Enhanced version of the UniversalSQLAgent with improved structure and organization.
"""

import os
import sys
import asyncio
import time
import warnings
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*Convert_system_message_to_human.*")

try:
    from langchain_community.utilities import SQLDatabase
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import ChatPromptTemplate
    from sqlalchemy import create_engine
except ImportError as e:
    print(f"Missing required packages for agent core: {e}")
    print("Run: pip install langchain langchain-community sqlalchemy")
    raise

# Import from existing structure (Phase 1 compatibility)
from ..config.database_config import DatabaseType, DatabaseConfig, DatabaseManager
from ..llm.models.llm_setup import LLMManager
from .prompt_manager import PromptManager

try:
    from ..utils.performance_monitor import PerformanceMonitor
    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITOR_AVAILABLE = False

try:
    from .response_formatter import ResponseFormatter
    RESPONSE_FORMATTER_AVAILABLE = True
except ImportError:
    RESPONSE_FORMATTER_AVAILABLE = False


class UniversalSQLAgent:
    """
    Enhanced Universal SQL Agent with improved structure and organization.
    
    This class provides a clean interface for SQL query processing with
    better separation of concerns and improved maintainability.
    """
    
    def __init__(self):
        """Initialize the Universal SQL Agent."""
        # Core components
        self.db = None
        self.llm = None
        self.agent = None
        self.conversation_history = []
        
        # Configuration
        self.db_config = None
        self.db_type = None
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()
        
        # Enhanced components
        self.prompt_manager = PromptManager()
        self.performance_monitor = PerformanceMonitor() if PERFORMANCE_MONITOR_AVAILABLE else None
        self.response_formatter = ResponseFormatter() if RESPONSE_FORMATTER_AVAILABLE else None
        
        # Statistics
        self.query_stats = {
            "total_queries": 0,
            "avg_response_time": 0.0
        } if not self.performance_monitor else None
        
        self._validation_stats = {
            "compliant_queries": 0
        } if not self.performance_monitor else None
    
    async def setup_database(self) -> bool:
        """Setup database connection with enhanced error handling."""
        try:
            self.db_type = self.db_manager.detect_database_type()
            print(f"🔍 Detected database type: {self.db_type.value.upper()}")
            
            self.db_config = self.db_manager.load_database_config(self.db_type)
            
            if not self.db_manager.is_driver_available(self.db_type):
                print(f"❌ No driver available for {self.db_type.value}")
                self.db_manager.show_driver_installation_help(self.db_type)
                return False
            
            print(f"Testing connection to {self.db_type.value.upper()} database...")
            if not self.db_manager.test_database_connection(self.db_config):
                print(f"❌ Database connection test failed")
                return False
            
            connection_string = self.db_manager.build_connection_string(self.db_config)
            engine = create_engine(connection_string)
            self.db = SQLDatabase(engine)
            
            tables = self.db.get_usable_table_names()
            if len(tables) <= 10:
                print(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
            else:
                print(f"📊 Found {len(tables)} tables: {', '.join(tables[:5])}, ... (and {len(tables)-5} more)")
                print(f"   First 10 tables: {', '.join(tables[:10])}")
                print(f"   Use 'tables' command to see all tables")
            
            print("✅ Database connection successful!")
            
            # Build semantic table index for intelligent table selection
            self.prompt_manager.build_semantic_table_index(self.db)
            
            return True
            
        except Exception as e:
            print(f"❌ Database setup failed: {str(e)}")
            return False
    
    def setup_llm(self) -> bool:
        """Setup Language Model with enhanced configuration."""
        try:
            success = self.llm_manager.setup_llm()
            return success
        except Exception as e:
            print(f"❌ LLM setup failed: {e}")
            return False
    
    def setup_agent(self) -> bool:
        """Setup the SQL agent with enhanced tools and configuration."""
        try:
            self.llm = self.llm_manager.get_llm()
            if not self.db or not self.llm:
                print("❌ Database or LLM not initialized")
                return False
            
            print("Setting up enhanced SQL agent with custom SQL cleaning...")
            
            # Use custom SQL toolkit with cleaned SQL queries and semantic table filtering
            try:
                from ..database.tools.custom_sql_tool import create_custom_sql_toolkit
            except ImportError:
                print("❌ Failed to import custom SQL toolkit")
                return False
            
            tools = create_custom_sql_toolkit(
                db=self.db, 
                llm=self.llm, 
                prompt_manager=self.prompt_manager
            )
            
            prompt = self.get_database_specific_chat_prompt()
            agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
            
            self.agent = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,
                max_execution_time=90,
                return_intermediate_steps=True,
                early_stopping_method="generate"
            )
            
            print("✅ Enhanced SQL agent ready with custom SQL cleaning and validation methodology!")
            return True
            
        except Exception as e:
            print(f"❌ Agent setup failed: {str(e)}")
            return False
    
    def get_database_specific_chat_prompt(self) -> ChatPromptTemplate:
        """Get database-specific chat prompt template."""
        db_names = {
            DatabaseType.POSTGRESQL: "PostgreSQL",
            DatabaseType.MYSQL: "MySQL",
            DatabaseType.SQLITE: "SQLite",
            DatabaseType.SQLSERVER: "SQL Server",
            DatabaseType.ORACLE: "Oracle",
            DatabaseType.MONGODB: "MongoDB"
        }
        
        database_name = db_names.get(self.db_type, "SQL")
        schema_info = None
        
        if self.db:
            try:
                schema_info = self.db.get_table_info()
            except Exception:
                schema_info = None
        
        system_message = self.prompt_manager.load_system_message(self.db_type, schema_info)
        human_message = self.prompt_manager.load_human_message(self.db_type)
        database_features = self.prompt_manager.load_database_features(self.db_type, schema_info)
        
        formatted_human_message = human_message.format(
            database_name=database_name,
            database_features=database_features,
            tools="{tools}",
            tool_names="{tool_names}",
            input="{input}",
            agent_scratchpad="{agent_scratchpad}"
        )
        
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", formatted_human_message)
        ])
        
        return chat_prompt
    
    async def process_question(self, question: str, lightweight: bool = False) -> Dict[str, Any]:
        """Process a natural language question and return structured response."""
        start_time = time.time()
        
        try:
            if not self.agent:
                return self._create_error_response("Agent not initialized. Please restart the application.")
            
            if not question or question.strip() == "":
                return self._create_error_response("Please provide a valid question.")
            
            # Security check for dangerous operations
            dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
            if any(keyword in question.lower() for keyword in dangerous_keywords):
                return self._create_error_response(
                    "I can only help with SELECT queries for data retrieval. Modification operations are not allowed."
                )
            
            print(f"\n🤔 Processing: {question}")
            print("⏳ Thinking...")
            
            # Update semantic context for table filtering
            self._update_semantic_context(question)
            
            # Build context
            context = ""
            if not lightweight and self.conversation_history:
                recent_context = self.conversation_history[-2:]
                context = "\nRecent conversation context:\n"
                for i, (q, a) in enumerate(recent_context, 1):
                    context += f"{i}. Q: {q[:50]}...\n   A: {a[:50]}...\n"
            
            # Determine if lightweight mode should be used
            lightweight_keywords = ['list', 'show', 'display', 'view', 'get', 'find', 'tables', 'schema']
            if not lightweight and any(keyword in question.lower() for keyword in lightweight_keywords):
                lightweight = True
                print("🚀 Auto-enabling lightweight mode for better performance")
            
            if lightweight:
                schema_context = "Use sql_db_list_tables and sql_db_schema tools to explore the database. ALWAYS add LIMIT 10-20 to your queries."
            else:
                schema_context = "Database schema analysis will be performed during query execution."
            
            # Build enhanced question
            enhanced_question = f"""Database Type: {self.db_type.value.upper()}
{context}

Schema Context:
{schema_context}

{question}"""
            
            # Execute query with retry logic
            max_retries = 2
            query_id = None
            
            if self.performance_monitor:
                query_id = self.performance_monitor.start_query_timer()
            
            query_start_time = time.time()
            
            for attempt in range(max_retries + 1):
                try:
                    result = await asyncio.to_thread(self.agent.invoke, {"input": enhanced_question})
                    break
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    print(f"\n⚠️ Attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(1)
            
            query_time = time.time() - query_start_time
            
            if self.performance_monitor and query_id:
                self.performance_monitor.end_query_timer(query_id)
            
            # Process response
            raw_response = ""
            if isinstance(result, dict):
                raw_response = result.get("output", str(result))
                
                if "agent stopped due to iteration limit" in raw_response.lower() or \
                   "agent stopped due to time limit" in raw_response.lower():
                    intermediate_steps = result.get("intermediate_steps", [])
                    if self.response_formatter:
                        extracted_info = self.response_formatter.extract_from_intermediate_steps(intermediate_steps)
                        if extracted_info:
                            raw_response = extracted_info
                        else:
                            raw_response = "I was able to process your query but encountered formatting issues. The query executed successfully, but I couldn't format the final response properly. Please try rephrasing your question for better results."
                    else:
                        raw_response = "I was able to process your query but encountered formatting issues. The query executed successfully, but I couldn't format the final response properly. Please try rephrasing your question for better results."
            else:
                raw_response = str(result)
            
            # Validate response format
            if self.response_formatter:
                is_compliant, format_score, format_issues = self.response_formatter.validate_agent_response_format(raw_response)
                format_validation = {
                    "format_score": format_score * 100,
                    "has_schema_exploration": is_compliant,
                    "has_validation_check": is_compliant,
                    "issues": format_issues
                }
            else:
                format_validation = {
                    "format_score": 75, 
                    "has_schema_exploration": False, 
                    "has_validation_check": False
                }
            
            if format_validation["format_score"] < 50:
                print(f"⚠️ Warning: Agent response format score: {format_validation['format_score']}/100")
                print("Agent may not be following prompt guidelines correctly")
            
            # Parse response
            if self.response_formatter:
                parsed_response = self.response_formatter.parse_agent_response(raw_response)
            else:
                parsed_response = raw_response
            
            # Create structured response
            total_time = time.time() - start_time
            
            if self.response_formatter:
                structured_response = self.response_formatter.create_structured_response(
                    content=parsed_response,
                    processing_time=total_time,
                    query_time=query_time
                )
            else:
                structured_response = self._create_structured_response(
                    content=parsed_response,
                    question=question,
                    processing_time=total_time,
                    query_time=query_time,
                    database_type=self.db_type.value if self.db_type else "unknown"
                )
            
            # Update conversation history
            self.conversation_history.append((question, structured_response["content"]))
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Update statistics
            if self.performance_monitor:
                self.performance_monitor.record_query_completion(
                    processing_time=total_time,
                    is_validation_compliant=format_validation.get("has_schema_exploration", False) and 
                    format_validation.get("has_validation_check", False)
                )
            else:
                if self.query_stats:
                    self.query_stats["total_queries"] += 1
                    prev_avg = self.query_stats["avg_response_time"]
                    total_queries = self.query_stats["total_queries"]
                    self.query_stats["avg_response_time"] = ((prev_avg * (total_queries - 1)) + total_time) / total_queries
                
                if self._validation_stats and format_validation["has_schema_exploration"] and format_validation["has_validation_check"]:
                    self._validation_stats['compliant_queries'] += 1
                    print("✅ Query followed enhanced validation methodology")
                elif format_validation["format_score"] < 70:
                    print("⚠️ Query may not be following enhanced validation methodology")
            
            print(f"\n✅ Query completed successfully")
            if total_time > 5.0:
                print(f"⏱️ Total processing time: {total_time:.2f}s (Query: {query_time:.2f}s)")
            
            return structured_response
            
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = f"❌ Error processing question: {str(e)}"
            print(error_msg)
            print(f"⏱️ Failed after {total_time:.2f}s")
            
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                error_message = f"Column not found. Please check the available columns using the 'tables' command. Error: {str(e)}"
            elif "table" in str(e).lower() and "does not exist" in str(e).lower():
                error_message = f"Table not found. Please check the available tables using the 'tables' command. Error: {str(e)}"
            else:
                error_message = f"An error occurred while processing your question. Please try rephrasing it or check the syntax. Error: {str(e)}"
            
            return self._create_error_response(error_message, processing_time=total_time)
    
    def _update_semantic_context(self, question: str):
        """Update the semantic context for table filtering tools."""
        if hasattr(self, 'agent') and self.agent and hasattr(self.agent, 'tools'):
            for tool in self.agent.tools:
                if hasattr(tool, 'update_question_context'):
                    tool.update_question_context(question)
    
    def _create_structured_response(self, content: str, question: str, processing_time: float,
                                  query_time: float, database_type: str) -> Dict[str, Any]:
        """Create a structured response with metadata."""
        content_analysis = self._analyze_content(content)
        validation_analysis = self._analyze_validation_quality(content)
        
        # Use helper method for formatter-dependent operations
        formatted_content = self._get_formatted_content(content, content_analysis)
        summary, suggestions, ui_components = self._get_response_components(
            content, content_analysis, validation_analysis, question
        )
        
        metadata = {
            "processing_time": round(processing_time, 2),
            "query_time": round(query_time, 2),
            "database_type": database_type,
            "content_type": content_analysis["type"],
            "has_data": content_analysis["has_data"],
            "record_count": content_analysis.get("record_count", 0),
            "validation_quality": validation_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        performance = self._get_performance_metrics(processing_time, validation_analysis)
        
        return {
            "status": "success",
            "content": formatted_content,
            "summary": summary,
            "metadata": metadata,
            "performance": performance,
            "suggestions": suggestions,
            "ui_components": ui_components
        }
    
    def _create_error_response(self, error_message: str, processing_time: float = 0.0) -> Dict[str, Any]:
        """Create a structured error response."""
        return {
            "status": "error",
            "content": error_message,
            "summary": "Query execution failed",
            "metadata": {
                "processing_time": round(processing_time, 2),
                "database_type": self.db_type.value if self.db_type else "unknown",
                "content_type": "error",
                "has_data": False,
                "timestamp": datetime.now().isoformat()
            },
            "performance": self._get_performance_metrics(processing_time),
            "suggestions": self._get_default_error_suggestions(),
            "ui_components": {
                "type": "error_message",
                "icon": "⚠️",
                "color": "error"
            }
        }
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content for response formatting."""
        analysis = {
            "type": "text",
            "has_data": False,
            "record_count": 0,
            "has_numbers": False,
            "has_lists": False,
            "has_tables": False,
            "is_summary": False
        }
        
        # Check for data patterns
        data_tuple_pattern = re.compile(r'\(\d+,.*?\)')
        data_bracket_pattern = re.compile(r'\[\d+,.*?\]')
        tuple_pattern = re.compile(r'\([^)]+\)')
        
        if data_tuple_pattern.search(content) or data_bracket_pattern.search(content):
            analysis["type"] = "data_results"
            analysis["has_data"] = True
            records = tuple_pattern.findall(content)
            analysis["record_count"] = len(records)
        
        # Check for list patterns
        list_number_pattern = re.compile(r'\d+\.\s+')
        list_paren_pattern = re.compile(r'\d+\)\s+')
        
        if list_number_pattern.search(content) or list_paren_pattern.search(content):
            analysis["has_lists"] = True
            if not analysis["has_data"]:
                analysis["type"] = "list"
        
        # Check for summary indicators
        summary_indicators = ['total', 'average', 'count', 'sum', 'analysis', 'insight', 'trend']
        if any(indicator in content.lower() for indicator in summary_indicators):
            analysis["is_summary"] = True
            if not analysis["has_data"] and not analysis["has_lists"]:
                analysis["type"] = "summary"
        
        # Check for numbers
        number_pattern = re.compile(r'\d+')
        if number_pattern.search(content):
            analysis["has_numbers"] = True
        
        return analysis
    
    def _get_formatted_content(self, content: str, content_analysis: Dict[str, Any]) -> str:
        """Helper method to get formatted content based on response formatter availability."""
        if self.response_formatter:
            return self.response_formatter.format_content_for_display(content, content_analysis)
        return content
    
    def _get_response_components(self, content: str, content_analysis: Dict[str, Any], 
                               validation_analysis: Dict[str, Any], question: str) -> tuple:
        """Helper method to get response components based on response formatter availability."""
        if self.response_formatter:
            summary = self.response_formatter.generate_summary(content, content_analysis, validation_analysis)
            suggestions = self.response_formatter.generate_suggestions(question, content_analysis, validation_analysis)
            ui_components = self.response_formatter.suggest_ui_components(content_analysis)
        else:
            summary = "Query executed successfully"
            suggestions = ["Check your query syntax", "Verify table and column names"]
            ui_components = {"type": "text", "icon": "📊", "color": "primary"}
        return summary, suggestions, ui_components
    
    def _get_performance_metrics(self, processing_time: float, validation_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Helper method to get performance metrics based on performance monitor availability."""
        base_performance = {"fast": processing_time < 2.0}
        
        if self.performance_monitor:
            return base_performance
        else:
            if validation_analysis:
                base_performance["validation_score"] = validation_analysis.get("score", 0)
            return base_performance
    
    def _get_default_error_suggestions(self) -> List[str]:
        """Helper method to get default error suggestions."""
        return [
            "Check your query syntax",
            "Verify table and column names",
            "Try a simpler query first",
            "Use the 'tables' command to see available data"
        ]
    
    def _analyze_validation_quality(self, content: str) -> Dict[str, Any]:
        """Analyze validation quality of the content."""
        if self.response_formatter:
            return self.response_formatter.analyze_validation_quality(content)
        else:
            # Fallback validation analysis
            return {
                "score": 50,
                "issues": [],
                "suggestions": ["Enable response formatter for detailed validation analysis"]
            }
    
    async def quick_query(self, question: str) -> Dict[str, Any]:
        """Process a question in lightweight mode."""
        return await self.process_question(question, lightweight=True)
    
    async def close(self):
        """Close the agent and cleanup resources."""
        print("🔒 Closing Universal SQL Agent...")
        
        # Show final performance statistics with validation metrics
        if self.performance_monitor:
            self.performance_monitor.print_performance_summary()
        elif self.query_stats and self.query_stats["total_queries"] > 0:
            print("\n📊 Final Performance Summary:")
            print(f"  Total Queries Processed: {self.query_stats['total_queries']}")
            print(f"  Average Response Time: {self.query_stats['avg_response_time']:.2f}s")
            
            if self._validation_stats and self._validation_stats.get('compliant_queries', 0) > 0:
                compliance_rate = (self._validation_stats['compliant_queries'] / self.query_stats['total_queries']) * 100
                print(f"  Validation Methodology Compliance: {compliance_rate:.1f}%")
        
        print("👋 Agent closed successfully!")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
