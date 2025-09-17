#!/usr/bin/env python3
"""
Universal SQL Agent - Enhanced Main Entry Point
A powerful AI agent for querying multiple database types using natural language.
Supports both legacy and new folder structure.
"""

import asyncio
import sys
import os
from typing import Optional

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


from src.agents.sql_agent import UniversalSQLAgent
from src.services.agent_service import AgentService


class UniversalSQLAgentApp:
    """Main application class for the Universal SQL Agent"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.agent: Optional[UniversalSQLAgent] = None
    
    async def initialize(self) -> bool:
        """Initialize the agent and all required components"""
        print("🚀 Initializing Universal SQL Agent...")
        
        try:
            # Initialize the agent
            self.agent = UniversalSQLAgent()
            
            # Setup database
            print("📊 Setting up database connection...")
            if not await self.agent.setup_database():
                print("❌ Failed to setup database. Please check your configuration.")
                return False
            
            # Setup LLM
            print("🤖 Setting up Language Model...")
            if not self.agent.setup_llm():
                print("❌ Failed to setup LLM. Please check your API keys.")
                return False
            
            # Setup agent
            print("⚙️ Setting up SQL agent...")
            if not self.agent.setup_agent():
                print("❌ Failed to setup agent.")
                return False
            
            print("✅ Universal SQL Agent initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {str(e)}")
            return False
    
    async def run_interactive(self):
        """Run the interactive SQL agent session"""
        if not self.agent:
            print("❌ Agent not initialized. Please run initialize() first.")
            return
        
        print("\n" + "="*60)
        print("🎯 Universal SQL Agent - Interactive Mode")
        print("="*60)
        print("Type your questions in natural language to query your database.")
        print("Commands:")
        print("  - 'tables' or 'show tables' - List all available tables")
        print("  - 'schema <table>' - Show schema for a specific table")
        print("  - 'help' - Show this help message")
        print("  - 'quit' or 'exit' - Exit the application")
        print("="*60)
        
        while True:
            try:
                # Get user input
                question = input("\n🤔 Ask a question: ").strip()
                
                # Handle special commands
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif question.lower() in ['help', 'h']:
                    self.show_help()
                    continue
                elif question.lower() in ['tables', 'show tables', 'list tables']:
                    await self.show_tables()
                    continue
                elif question.lower().startswith('schema '):
                    table_name = question[7:].strip()
                    await self.show_schema(table_name)
                    continue
                elif not question:
                    continue
                
                # Process the question
                print("⏳ Processing your question...")
                result = await self.agent.process_question(question)
                
                # Display result
                self.display_result(result)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def show_help(self):
        """Show help information"""
        print("\n📚 Universal SQL Agent Help:")
        print("This agent can help you query your database using natural language.")
        print("\nExamples:")
        print("  - 'Show me all customers from New York'")
        print("  - 'What are the top 10 products by sales?'")
        print("  - 'How many orders were placed last month?'")
        print("  - 'List all tables in the database'")
        print("\nCommands:")
        print("  - tables: List all available tables")
        print("  - schema <table>: Show detailed schema for a table")
        print("  - help: Show this help")
        print("  - quit: Exit the application")
    
    async def show_tables(self):
        """Show all available tables"""
        if not self.agent or not self.agent.db:
            print("❌ Database not connected")
            return
        
        try:
            tables = self.agent.db.get_usable_table_names()
            if tables:
                print(f"\n📊 Found {len(tables)} tables:")
                for i, table in enumerate(tables, 1):
                    print(f"  {i}. {table}")
            else:
                print("❌ No tables found in the database")
        except Exception as e:
            print(f"❌ Error listing tables: {str(e)}")
    
    async def show_schema(self, table_name: str):
        """Show schema for a specific table"""
        if not self.agent or not self.agent.db:
            print("❌ Database not connected")
            return
        
        try:
            schema_info = self.agent.db.get_table_info([table_name])
            print(f"\n📋 Schema for table '{table_name}':")
            print("-" * 50)
            print(schema_info)
        except Exception as e:
            print(f"❌ Error showing schema for '{table_name}': {str(e)}")
    
    def display_result(self, result: dict):
        """Display query result in a formatted way"""
        if result.get("status") == "error":
            print(f"\n❌ Error: {result.get('content', 'Unknown error')}")
            if result.get("suggestions"):
                print("\n💡 Suggestions:")
                for suggestion in result["suggestions"]:
                    print(f"  - {suggestion}")
        else:
            print(f"\n✅ Result:")
            print("-" * 50)
            print(result.get("content", "No content"))
            
            # Show metadata if available
            metadata = result.get("metadata", {})
            if metadata:
                print(f"\n📊 Query executed in {metadata.get('processing_time', 0):.2f}s")
                if metadata.get("record_count", 0) > 0:
                    print(f"📈 Records returned: {metadata['record_count']}")
    
    async def close(self):
        """Close the agent and cleanup resources"""
        if self.agent:
            await self.agent.close()


async def main():
    """Main entry point"""
    app = UniversalSQLAgentApp()
    
    try:
        # Initialize the application
        if not await app.initialize():
            print("❌ Failed to initialize the application. Exiting.")
            return
        
        # Run interactive session
        await app.run_interactive()
        
    except Exception as e:
        print(f"❌ Application error: {str(e)}")
    finally:
        # Cleanup
        await app.close()


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())
