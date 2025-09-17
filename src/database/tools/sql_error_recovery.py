#!/usr/bin/env python3
"""
SQL Error Recovery Engine
Advanced error detection and automatic correction for SQL queries.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import difflib
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Classification of SQL error types for targeted recovery."""
    SYNTAX_ERROR = "syntax_error"
    COLUMN_NOT_FOUND = "column_not_found"
    TABLE_NOT_FOUND = "table_not_found"
    FUNCTION_ERROR = "function_error"
    TYPE_MISMATCH = "type_mismatch"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    CONNECTION_ERROR = "connection_error"
    CONSTRAINT_VIOLATION = "constraint_violation"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class ErrorPattern:
    """Represents a specific error pattern and its recovery strategy."""
    pattern: str
    error_type: ErrorType
    description: str
    auto_fix: bool = True
    confidence: float = 0.8
    recovery_function: Optional[str] = None

@dataclass
class RecoveryResult:
    """Result of an error recovery attempt."""
    success: bool
    corrected_query: Optional[str] = None
    error_type: Optional[ErrorType] = None
    corrections_applied: List[str] = None
    confidence: float = 0.0
    suggestion: Optional[str] = None
    original_error: Optional[str] = None

class SQLErrorRecoveryEngine:
    """
    Advanced SQL error recovery engine with pattern-based detection
    and automatic query correction capabilities.
    """
    
    def __init__(self, db_connection=None):
        self.db_connection = db_connection
        self.error_patterns = self._initialize_error_patterns()
        self.recovery_stats = {
            "total_errors": 0,
            "successful_recoveries": 0,
            "recovery_attempts_by_type": {},
            "common_fixes": {},
            "last_recovery": None
        }
        self.schema_cache = {}
        self.table_cache = []
        self.column_cache = {}
        
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize comprehensive error patterns for various database systems."""
        return [
            # PostgreSQL Patterns
            ErrorPattern(
                pattern=r'column "([^"]+)" does not exist',
                error_type=ErrorType.COLUMN_NOT_FOUND,
                description="Column name not found",
                recovery_function="fix_column_name"
            ),
            ErrorPattern(
                pattern=r'relation "([^"]+)" does not exist',
                error_type=ErrorType.TABLE_NOT_FOUND,
                description="Table name not found",
                recovery_function="fix_table_name"
            ),
            ErrorPattern(
                pattern=r'syntax error at or near "([^"]*)"',
                error_type=ErrorType.SYNTAX_ERROR,
                description="SQL syntax error",
                recovery_function="fix_syntax_error"
            ),
            ErrorPattern(
                pattern=r'function ([^\s(]+)\([^)]*\) does not exist',
                error_type=ErrorType.FUNCTION_ERROR,
                description="Function not found or wrong signature",
                recovery_function="fix_function_error"
            ),
            
            # MySQL Patterns
            ErrorPattern(
                pattern=r"Unknown column '([^']+)' in '([^']+)'",
                error_type=ErrorType.COLUMN_NOT_FOUND,
                description="MySQL column not found",
                recovery_function="fix_column_name"
            ),
            ErrorPattern(
                pattern=r"Table '([^']+)' doesn't exist",
                error_type=ErrorType.TABLE_NOT_FOUND,
                description="MySQL table not found",
                recovery_function="fix_table_name"
            ),
            
            # SQL Server Patterns
            ErrorPattern(
                pattern=r"Invalid column name '([^']+)'",
                error_type=ErrorType.COLUMN_NOT_FOUND,
                description="SQL Server column not found",
                recovery_function="fix_column_name"
            ),
            ErrorPattern(
                pattern=r"Invalid object name '([^']+)'",
                error_type=ErrorType.TABLE_NOT_FOUND,
                description="SQL Server table not found",
                recovery_function="fix_table_name"
            ),
            
            # Generic Patterns
            ErrorPattern(
                pattern=r'invalid input syntax for (?:type )?(\w+): "([^"]*)"',
                error_type=ErrorType.TYPE_MISMATCH,
                description="Type conversion error",
                recovery_function="fix_type_mismatch"
            ),
            ErrorPattern(
                pattern=r'permission denied for (?:relation|table) (\w+)',
                error_type=ErrorType.PERMISSION_ERROR,
                description="Permission denied",
                auto_fix=False
            ),
            ErrorPattern(
                pattern=r'canceling statement due to statement timeout',
                error_type=ErrorType.TIMEOUT_ERROR,
                description="Query timeout",
                recovery_function="optimize_for_timeout"
            ),
            
            # Common SQL Syntax Errors
            ErrorPattern(
                pattern=r'GROUP BY position (\d+) is not in select list',
                error_type=ErrorType.SYNTAX_ERROR,
                description="GROUP BY column not in SELECT",
                recovery_function="fix_group_by_error"
            ),
            ErrorPattern(
                pattern=r'must appear in the GROUP BY clause or be used in an aggregate function',
                error_type=ErrorType.SYNTAX_ERROR,
                description="Column not in GROUP BY",
                recovery_function="fix_aggregate_error"
            ),
        ]
    
    def analyze_error(self, error_message: str, query: str) -> Tuple[ErrorType, Dict[str, Any]]:
        """Analyze an error message to determine type and extract relevant information."""
        error_info = {
            "original_error": error_message,
            "query": query,
            "matches": [],
            "confidence": 0.0
        }
        
        best_match = None
        highest_confidence = 0.0
        
        for pattern in self.error_patterns:
            match = re.search(pattern.pattern, error_message, re.IGNORECASE)
            if match:
                confidence = pattern.confidence
                error_info["matches"].append({
                    "pattern": pattern.pattern,
                    "groups": match.groups(),
                    "confidence": confidence,
                    "error_type": pattern.error_type,
                    "recovery_function": pattern.recovery_function
                })
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = pattern
        
        if best_match:
            error_info["confidence"] = highest_confidence
            return best_match.error_type, error_info
        
        return ErrorType.UNKNOWN_ERROR, error_info
    
    def recover_from_error(self, error_message: str, query: str) -> RecoveryResult:
        """Main recovery method that attempts to fix SQL errors automatically."""
        self.recovery_stats["total_errors"] += 1
        
        error_type, error_info = self.analyze_error(error_message, query)
        
        # Track recovery attempts by type
        type_name = error_type.value
        self.recovery_stats["recovery_attempts_by_type"][type_name] = \
            self.recovery_stats["recovery_attempts_by_type"].get(type_name, 0) + 1
        
        # Find the best recovery strategy
        best_match = None
        for match in error_info.get("matches", []):
            if match["error_type"] == error_type and match.get("recovery_function"):
                best_match = match
                break
        
        if not best_match:
            return RecoveryResult(
                success=False,
                error_type=error_type,
                original_error=error_message,
                suggestion="No automatic recovery available for this error type."
            )
        
        # Apply the recovery function
        recovery_function = best_match["recovery_function"]
        try:
            if hasattr(self, recovery_function):
                corrected_query, corrections = getattr(self, recovery_function)(
                    query, error_message, best_match["groups"]
                )
                
                if corrected_query and corrected_query != query:
                    self.recovery_stats["successful_recoveries"] += 1
                    
                    # Track common fixes
                    for correction in corrections:
                        self.recovery_stats["common_fixes"][correction] = \
                            self.recovery_stats["common_fixes"].get(correction, 0) + 1
                    
                    result = RecoveryResult(
                        success=True,
                        corrected_query=corrected_query,
                        error_type=error_type,
                        corrections_applied=corrections,
                        confidence=best_match["confidence"],
                        original_error=error_message
                    )
                    
                    self.recovery_stats["last_recovery"] = {
                        "timestamp": datetime.now().isoformat(),
                        "error_type": error_type.value,
                        "corrections": corrections,
                        "success": True
                    }
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Error in recovery function {recovery_function}: {e}")
        
        return RecoveryResult(
            success=False,
            error_type=error_type,
            original_error=error_message,
            confidence=best_match["confidence"],
            suggestion=f"Could not automatically fix {error_type.value}. Manual intervention required."
        )
    
    def fix_column_name(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Fix column name errors using fuzzy matching against schema."""
        if not groups:
            return query, []
        
        invalid_column = groups[0]
        corrections = []
        
        # Get available columns from cache or database
        available_columns = self._get_available_columns(query)
        
        if not available_columns:
            # If no columns available from schema, use common column name fixes
            common_fixes = {
                'nam': 'name',
                'emai': 'email',
                'user_i': 'user_id',
                'product_i': 'product_id',
                'id_user': 'user_id',
                'id_product': 'product_id',
                'usr': 'user',
                'prod': 'product'
            }
            
            if invalid_column.lower() in common_fixes:
                best_match = common_fixes[invalid_column.lower()]
                corrected_query = re.sub(
                    rf'\b{re.escape(invalid_column)}\b',
                    best_match,
                    query,
                    flags=re.IGNORECASE
                )
                corrections.append(f"Replaced '{invalid_column}' with '{best_match}'")
                return corrected_query, corrections
            
            return query, []
        
        # Find closest match using fuzzy string matching
        closest_matches = difflib.get_close_matches(
            invalid_column, available_columns, n=3, cutoff=0.6
        )
        
        if closest_matches:
            best_match = closest_matches[0]
            corrected_query = re.sub(
                rf'\b{re.escape(invalid_column)}\b',
                best_match,
                query,
                flags=re.IGNORECASE
            )
            corrections.append(f"Replaced '{invalid_column}' with '{best_match}'")
            return corrected_query, corrections
        
        # If fuzzy matching fails, try common column name patterns
        common_fixes = {
            'nam': 'name',
            'emai': 'email', 
            'user_i': 'user_id',
            'product_i': 'product_id'
        }
        
        if invalid_column.lower() in common_fixes:
            best_match = common_fixes[invalid_column.lower()]
            corrected_query = re.sub(
                rf'\b{re.escape(invalid_column)}\b',
                best_match,
                query,
                flags=re.IGNORECASE
            )
            corrections.append(f"Replaced '{invalid_column}' with '{best_match}' (common pattern)")
            return corrected_query, corrections
        
        return query, []
    
    def fix_table_name(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Fix table name errors using fuzzy matching against available tables."""
        if not groups:
            return query, []
        
        invalid_table = groups[0]
        corrections = []
        
        # Get available tables
        available_tables = self._get_available_tables()
        
        if not available_tables:
            return query, []
        
        # Find closest match
        closest_matches = difflib.get_close_matches(
            invalid_table, available_tables, n=3, cutoff=0.6
        )
        
        if closest_matches:
            best_match = closest_matches[0]
            corrected_query = re.sub(
                rf'\b{re.escape(invalid_table)}\b',
                best_match,
                query,
                flags=re.IGNORECASE
            )
            corrections.append(f"Replaced table '{invalid_table}' with '{best_match}'")
            return corrected_query, corrections
        
        return query, []
    
    def fix_syntax_error(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Fix common SQL syntax errors."""
        corrections = []
        corrected_query = query
        
        # Common syntax fixes
        syntax_fixes = [
            # Missing commas
            (r'SELECT\s+(\w+)\s+(\w+)\s+FROM', r'SELECT \1, \2 FROM', "Added missing comma in SELECT"),
            # Wrong quote types
            (r"'(\d+)'", r'\1', "Removed quotes from numeric literal"),
            # Missing parentheses in functions
            (r'(\w+)\s*\(\s*\)', r'\1()', "Fixed function parentheses"),
            # LIMIT without number
            (r'LIMIT\s*$', r'LIMIT 100', "Added default LIMIT value"),
            # Missing semicolon (if needed)
            (r'(?<!;)\s*$', r';', "Added missing semicolon"),
        ]
        
        for pattern, replacement, description in syntax_fixes:
            if re.search(pattern, corrected_query, re.IGNORECASE):
                new_query = re.sub(pattern, replacement, corrected_query, flags=re.IGNORECASE)
                if new_query != corrected_query:
                    corrected_query = new_query
                    corrections.append(description)
                    break  # Apply one fix at a time
        
        return corrected_query, corrections
    
    def fix_function_error(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Fix function-related errors."""
        corrections = []
        corrected_query = query
        
        # Common function fixes
        function_fixes = {
            'len': 'LENGTH',
            'str': 'CAST(... AS TEXT)',
            'int': 'CAST(... AS INTEGER)',
            'substr': 'SUBSTRING',
            'isnull': 'COALESCE',
            'ifnull': 'COALESCE',
            'now': 'NOW()',
            'today': 'CURRENT_DATE',
        }
        
        if groups:
            wrong_function = groups[0]
            for wrong, correct in function_fixes.items():
                if wrong.lower() == wrong_function.lower():
                    corrected_query = re.sub(
                        rf'\b{re.escape(wrong_function)}\b',
                        correct,
                        corrected_query,
                        flags=re.IGNORECASE
                    )
                    corrections.append(f"Replaced function '{wrong_function}' with '{correct}'")
                    break
        
        return corrected_query, corrections
    
    def fix_type_mismatch(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Fix type conversion errors."""
        corrections = []
        corrected_query = query
        
        if len(groups) >= 2:
            target_type = groups[0]
            invalid_value = groups[1]
            
            # Common type conversion fixes
            if target_type.lower() in ['integer', 'int', 'bigint']:
                # Try to extract numeric part
                numeric_match = re.search(r'\d+', invalid_value)
                if numeric_match:
                    numeric_value = numeric_match.group()
                    corrected_query = corrected_query.replace(
                        f"'{invalid_value}'", numeric_value
                    )
                    corrections.append(f"Converted '{invalid_value}' to numeric {numeric_value}")
            
            elif target_type.lower() in ['date', 'timestamp']:
                # Add proper date casting
                corrected_query = re.sub(
                    rf"'{re.escape(invalid_value)}'",
                    f"'{invalid_value}'::DATE",
                    corrected_query
                )
                corrections.append(f"Added date casting for '{invalid_value}'")
        
        return corrected_query, corrections
    
    def optimize_for_timeout(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Optimize queries that timeout."""
        corrections = []
        corrected_query = query
        
        # Add LIMIT if missing
        if 'LIMIT' not in corrected_query.upper():
            corrected_query = corrected_query.rstrip(';') + ' LIMIT 1000;'
            corrections.append("Added LIMIT 1000 to prevent timeout")
        
        # Replace SELECT * with specific columns (basic heuristic)
        if 'SELECT *' in corrected_query.upper():
            # This is a simplified approach - in practice, you'd need schema info
            corrected_query = re.sub(
                r'SELECT\s+\*',
                'SELECT id, name',  # Default fallback columns
                corrected_query,
                flags=re.IGNORECASE
            )
            corrections.append("Replaced SELECT * with specific columns")
        
        return corrected_query, corrections
    
    def fix_group_by_error(self, query: str, error_message: str, groups: Tuple) -> Tuple[str, List[str]]:
        """Fix GROUP BY related errors."""
        corrections = []
        corrected_query = query
        
        # Extract SELECT columns and ensure they're in GROUP BY
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', corrected_query, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_part = select_match.group(1)
            # Simple heuristic: add non-aggregate columns to GROUP BY
            # This is a basic implementation - real-world would be more sophisticated
            columns = [col.strip() for col in select_part.split(',')]
            non_aggregate_cols = [col for col in columns if not any(func in col.upper() 
                                for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'])]
            
            if non_aggregate_cols:
                group_by_cols = ', '.join(non_aggregate_cols[:3])  # Limit to first 3
                if 'GROUP BY' in corrected_query.upper():
                    corrected_query = re.sub(
                        r'GROUP BY.*?(?=ORDER|LIMIT|HAVING|$)',
                        f'GROUP BY {group_by_cols} ',
                        corrected_query,
                        flags=re.IGNORECASE
                    )
                else:
                    corrected_query = corrected_query.rstrip(';') + f' GROUP BY {group_by_cols};'
                
                corrections.append(f"Added/fixed GROUP BY clause with columns: {group_by_cols}")
        
        return corrected_query, corrections
    
    def _get_available_tables(self) -> List[str]:
        """Get list of available tables from database or cache."""
        if self.table_cache:
            return self.table_cache
        
        if self.db_connection:
            try:
                tables = self.db_connection.get_usable_table_names()
                self.table_cache = tables
                return tables
            except Exception as e:
                logger.warning(f"Could not fetch table names: {e}")
        
        return []
    
    def _get_available_columns(self, query: str) -> List[str]:
        """Extract available columns from query context or schema."""
        # This is a simplified implementation
        # In practice, you'd parse the query to identify tables and get their columns
        
        # Extract table names from the query
        table_matches = re.findall(r'FROM\s+(\w+)', query, re.IGNORECASE)
        table_matches.extend(re.findall(r'JOIN\s+(\w+)', query, re.IGNORECASE))
        
        all_columns = []
        for table in table_matches:
            columns = self._get_table_columns(table)
            all_columns.extend(columns)
        
        return list(set(all_columns))  # Remove duplicates
    
    def _get_table_columns(self, table_name: str) -> List[str]:
        """Get columns for a specific table."""
        if table_name in self.column_cache:
            return self.column_cache[table_name]
        
        if self.db_connection:
            try:
                # Try to get table info
                table_info = self.db_connection.get_table_info([table_name])
                # Parse column names from table info (simplified)
                columns = re.findall(r'(\w+)\s+(?:VARCHAR|INTEGER|TEXT|NUMERIC|BOOLEAN|DATE|TIMESTAMP)', 
                                   table_info, re.IGNORECASE)
                self.column_cache[table_name] = columns
                return columns
            except Exception as e:
                logger.warning(f"Could not fetch columns for table {table_name}: {e}")
        
        return []
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get comprehensive recovery statistics."""
        total_errors = self.recovery_stats["total_errors"]
        successful_recoveries = self.recovery_stats["successful_recoveries"]
        
        return {
            **self.recovery_stats,
            "success_rate": (successful_recoveries / max(total_errors, 1)) * 100,
            "most_common_error_types": dict(sorted(
                self.recovery_stats["recovery_attempts_by_type"].items(),
                key=lambda x: x[1], reverse=True
            )[:5]),
            "most_effective_fixes": dict(sorted(
                self.recovery_stats["common_fixes"].items(),
                key=lambda x: x[1], reverse=True
            )[:5])
        }
    
    def reset_stats(self):
        """Reset recovery statistics."""
        self.recovery_stats = {
            "total_errors": 0,
            "successful_recoveries": 0,
            "recovery_attempts_by_type": {},
            "common_fixes": {},
            "last_recovery": None
        }
        logger.info("Error recovery statistics reset.")
