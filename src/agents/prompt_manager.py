#!/usr/bin/env python3
"""
Prompt Manager Module
Manages modular prompt templates with dynamic composition for different database types and industry contexts.
"""

import os
import re
from typing import Dict, Any, Optional, List

# Add project root to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..config.database_config import DatabaseType

# Import semantic table selector if available
try:
    from ..utils.semantic_table_selector import create_semantic_table_selector, SemanticTableSelector
    SEMANTIC_TABLE_SELECTOR_AVAILABLE = True
except ImportError:
    try:
        from core.semantic_table_selector import create_semantic_table_selector, SemanticTableSelector
        SEMANTIC_TABLE_SELECTOR_AVAILABLE = True
    except ImportError:
        SEMANTIC_TABLE_SELECTOR_AVAILABLE = False


class PromptManager:
    """Manages modular prompt templates with dynamic composition for different database types and industry contexts"""

    def __init__(self):
        # Get prompts directory relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.prompts_dir = os.path.join(project_root, 'prompts')
        self.industries_dir = os.path.join(self.prompts_dir, 'industries')
        self.detected_industry = None
        self.schema_context = None
        self.available_industries = self._get_available_industries()

        self._template_cache = {}
        self._industry_cache = {}
        self._database_cache = {}

        # Initialize semantic table selector if available
        self.semantic_table_selector = None
        if SEMANTIC_TABLE_SELECTOR_AVAILABLE:
            try:
                self.semantic_table_selector = create_semantic_table_selector()
            except Exception as e:
                print(f"Failed to initialize semantic table selector: {e}")
                self.semantic_table_selector = None

    def _get_available_industries(self) -> list:
        """Get list of available industry prompt files."""
        try:
            if os.path.exists(self.industries_dir):
                return [f.replace('.md', '') for f in os.listdir(self.industries_dir) if f.endswith('.md')]
            return []
        except Exception:
            return []

    def load_system_message(self, db_type: DatabaseType = None, schema_info: str = None) -> str:
        """Load and compose system message with industry and database-specific content."""
        cache_key = 'system_message_base'
        if cache_key not in self._template_cache:
            with open(os.path.join(self.prompts_dir, 'system_message.md'), 'r', encoding='utf-8') as f:
                self._template_cache[cache_key] = f.read()

        base_message = self._template_cache[cache_key]

        if schema_info and not self.detected_industry:
            self.detected_industry = self.detect_industry_from_schema(schema_info)
            self.schema_context = schema_info
        if self.detected_industry:
            industry_content = self._load_industry_content(self.detected_industry)
            if industry_content:
                industry_header = f"\n\n## 🎯 INDUSTRY INTELLIGENCE: {self.detected_industry.upper()}"
                industry_note = f"\nYou are working with a {self.detected_industry} database. Apply the following industry-specific expertise:\n"
                base_message += industry_header + industry_note + industry_content

        if db_type:
            db_features = self._load_database_content(db_type)
            if db_features:
                db_header = f"\n\n## 🔧 DATABASE-SPECIFIC FEATURES: {db_type.value.upper()}"
                base_message += db_header + "\n" + db_features

        return base_message

    def load_human_message(self, db_type: DatabaseType = None) -> str:
        """Load human message template."""
        cache_key = 'human_message_base'
        if cache_key not in self._template_cache:
            with open(os.path.join(self.prompts_dir, 'human_message.md'), 'r', encoding='utf-8') as f:
                self._template_cache[cache_key] = f.read()
        return self._template_cache[cache_key]

    def get_optimized_table_list(self, question: str, available_tables: List[str]) -> List[str]:
        """
        Get optimized list of tables using semantic selection if available,
        otherwise fall back to simple truncation.

        Args:
            question: User's natural language question
            available_tables: List of all available table names

        Returns:
            List of selected table names, optimized for the question
        """
        # Use semantic table selector if available and enabled
        if (self.semantic_table_selector and
            self.semantic_table_selector.enabled and
            len(available_tables) > 3):  # Only use for databases with multiple tables

            try:
                selected_tables = self.semantic_table_selector.select_relevant_tables(
                    question=question,
                    available_tables=available_tables
                )

                if selected_tables:
                    print(f"🧠 Semantic selection: {len(selected_tables)} tables from {len(available_tables)} available")
                    return selected_tables

            except Exception as e:
                print(f"⚠️ Semantic table selection failed: {e}")
                print("   Falling back to simple table selection")

        # Fallback to simple truncation
        max_tables = 10
        if len(available_tables) > max_tables:
            print(f"📊 Using first {max_tables} tables from {len(available_tables)} available")
            return available_tables[:max_tables]
        else:
            return available_tables

    def build_semantic_table_index(self, db) -> None:
        """
        Build semantic embeddings for database tables asynchronously.

        Args:
            db: SQLDatabase instance to extract table information from
        """
        if not self.semantic_table_selector or not self.semantic_table_selector.enabled:
            return

        try:
            # Get table names
            table_names = db.get_usable_table_names()
            if not table_names:
                print("   No tables found for indexing")
                return

            # Check if we have valid cached embeddings
            if self.semantic_table_selector.is_cache_valid_for_tables(table_names):
                print(f"✅ Using cached semantic embeddings for {len(table_names)} tables")
                return

            print(f"🧠 Preparing semantic table index for {len(table_names)} tables...")

            # Extract table information for embedding generation
            table_info = {}
            processed_count = 0

            for table_name in table_names:
                try:
                    # Get table schema information with error handling
                    schema_info = db.get_table_info_no_throw([table_name])

                    # Parse column names from schema info
                    columns = self._extract_column_names_from_schema(schema_info)

                    table_info[table_name] = {
                        "columns": columns,
                        "description": f"Database table {table_name}",
                        "schema_info": schema_info
                    }
                    processed_count += 1

                    # Show progress for large databases
                    if len(table_names) > 50 and processed_count % 50 == 0:
                        print(f"   📊 Prepared {processed_count}/{len(table_names)} tables for indexing...")

                except Exception as e:
                    # Log warning but continue processing other tables
                    print(f"   ⚠️ Skipped table {table_name}: {str(e)[:100]}...")
                    continue

            # Start asynchronous indexing
            if table_info:
                print(f"🚀 Starting background semantic indexing for {len(table_info)} tables...")
                print("   💡 Server will start immediately - indexing continues in background")

                # Define progress callback
                def progress_callback(status):
                    if status.get("status") == "completed":
                        successful = status.get("successful_tables", 0)
                        total = status.get("total_tables", 0)
                        print(f"✅ Semantic table indexing completed: {successful}/{total} tables indexed successfully")
                    elif status.get("status") == "failed":
                        print(f"❌ Semantic table indexing failed: {status.get('error_message', 'Unknown error')}")

                # Set progress callback and start async indexing
                self.semantic_table_selector.progress_callback = progress_callback
                self.semantic_table_selector.build_table_embeddings_async(table_info)

            else:
                print("   ⚠️ No table information available for indexing")

        except Exception as e:
            print(f"⚠️ Failed to prepare semantic table index: {e}")

    def _extract_column_names_from_schema(self, schema_info: str) -> List[str]:
        """Extract column names from schema information string with enhanced error handling."""
        columns = []
        try:
            if not schema_info or not isinstance(schema_info, str):
                return []

            # Enhanced pattern matching for different schema formats
            column_patterns = [
                # Standard SQL CREATE TABLE format
                r'^\s*(\w+)\s+(?:INTEGER|VARCHAR|TEXT|BOOLEAN|TIMESTAMP|DATE|DECIMAL|FLOAT|DOUBLE|BIGINT|SMALLINT|CHAR|BLOB|CLOB)',
                # Column: format
                r'Column\s+[\'"`]?(\w+)[\'"`]?',
                # Quoted column names
                r'[\'"`](\w+)[\'"`]\s+(?:INTEGER|VARCHAR|TEXT|BOOLEAN|TIMESTAMP|DATE|DECIMAL|FLOAT|DOUBLE|BIGINT|SMALLINT|CHAR|BLOB|CLOB)',
                # Simple word patterns (fallback)
                r'^\s*(\w+)\s+\w+',
            ]

            # Split schema info into lines for better parsing
            lines = schema_info.split('\n')

            for line in lines:
                line = line.strip()
                if not line or line.startswith('--') or line.startswith('/*'):
                    continue  # Skip comments

                # Try each pattern
                for pattern in column_patterns:
                    matches = re.findall(pattern, line, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]  # Take first group if tuple
                        if match and match.isalnum() and len(match) > 1:
                            columns.append(match)

            # Remove duplicates while preserving order
            seen = set()
            unique_columns = []
            for col in columns:
                col_lower = col.lower()
                if col_lower not in seen and col_lower not in ['table', 'create', 'primary', 'key', 'foreign', 'constraint']:
                    seen.add(col_lower)
                    unique_columns.append(col)

            # Limit to reasonable number of columns
            return unique_columns[:25]

        except Exception as e:
            # Suppress detailed error for common issues
            if "circular" in str(e).lower() or "foreign key" in str(e).lower():
                return []  # Silently handle circular dependency issues
            print(f"   Warning: Could not extract column names: {str(e)[:100]}...")
            return []

    def _load_industry_content(self, industry: str) -> str:
        """Load industry-specific content from file."""
        if industry in self._industry_cache:
            return self._industry_cache[industry]
        industry_file = os.path.join(self.industries_dir, f"{industry}.md")
        if os.path.exists(industry_file):
            with open(industry_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self._industry_cache[industry] = content
                return content
        self._industry_cache[industry] = ""
        return ""

    def _load_database_content(self, db_type: DatabaseType) -> str:
        """Load database-specific content from file."""
        db_key = db_type.value
        if db_key in self._database_cache:
            return self._database_cache[db_key]
        db_file_map = {
            DatabaseType.POSTGRESQL: 'postgresql_prompt.md',
            DatabaseType.MYSQL: 'mysql_prompt.md',
            DatabaseType.SQLITE: 'sqlite_prompt.md',
            DatabaseType.SQLSERVER: 'sqlserver_prompt.md',
            DatabaseType.ORACLE: 'oracle_prompt.md',
            DatabaseType.MONGODB: 'mongodb_prompt.md'
        }
        db_file = db_file_map.get(db_type)
        if db_file:
            db_path = os.path.join(self.prompts_dir, db_file)
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self._database_cache[db_key] = content
                    return content
        self._database_cache[db_key] = ""
        return ""

    def _extract_industry_keywords(self, industry_content: str) -> list:
        """Extract industry detection keywords from content."""
        keywords = []
        lines = industry_content.split('\n')
        for line in lines:
            if line.startswith('## Industry Detection Keywords:'):
                keyword_line = lines[lines.index(line) + 1] if lines.index(line) + 1 < len(lines) else ""
                keywords = [k.strip() for k in keyword_line.split(',') if k.strip()]
                break
        return keywords

    def detect_industry_from_schema(self, schema_info: str) -> Optional[str]:
        """Detect industry type from database schema information."""
        if not schema_info:
            return None
        schema_lower = schema_info.lower()
        industry_scores = {}
        for industry in self.available_industries:
            industry_content = self._load_industry_content(industry)
            if industry_content:
                keywords = self._extract_industry_keywords(industry_content)
                if keywords:
                    score = sum(1 for keyword in keywords if keyword.lower() in schema_lower)
                    if score > 0:
                        industry_scores[industry] = score
        if industry_scores:
            best_industry = max(industry_scores, key=industry_scores.get)
            if industry_scores[best_industry] >= 2:
                print(f"🎯 Detected industry: {best_industry} (confidence score: {industry_scores[best_industry]})")
                return best_industry
            else:
                print(f"⚠️ Low confidence industry detection: {best_industry} (score: {industry_scores[best_industry]})")
        return None

    def load_database_features(self, db_type: DatabaseType, schema_info: str = None) -> str:
        """Load database-specific features and industry context."""
        if schema_info and not self.detected_industry:
            self.detected_industry = self.detect_industry_from_schema(schema_info)
            self.schema_context = schema_info
        base_features = self._load_database_content(db_type)
        if base_features:
            lines = base_features.split('\n')
            feature_lines = []
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    feature_lines.append(line.strip())
            base_features = '\n'.join(feature_lines[:10])
        else:
            base_features = f"Use {db_type.value} standard syntax and features."
        if self.detected_industry:
            industry_context = self._get_industry_context(self.detected_industry)
            if industry_context:
                base_features += f"\n\n## Industry-Specific Context ({self.detected_industry.title()})\n{industry_context}"
        return base_features

    def _get_industry_context(self, industry: str) -> str:
        """Get industry-specific context."""
        industry_content = self.load_industry_intelligence(industry)
        if industry_content:
            return industry_content
        return ""

    def load_industry_intelligence(self, industry: str) -> str:
        """Load industry intelligence content."""
        industry_file = os.path.join(self.industries_dir, f"{industry}.md")
        if os.path.exists(industry_file):
            with open(industry_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

