#!/usr/bin/env python3
"""
Query Correction Service
High-level query correction and optimization service that works with the Error Recovery Engine.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from .sql_error_recovery import SQLErrorRecoveryEngine, RecoveryResult, ErrorType

logger = logging.getLogger(__name__)

class CorrectionStrategy(Enum):
    """Different correction strategies available."""
    CONSERVATIVE = "conservative"  # Only safe, high-confidence fixes
    MODERATE = "moderate"         # Balanced approach
    AGGRESSIVE = "aggressive"     # Try more experimental fixes

@dataclass
class CorrectionAttempt:
    """Represents a single correction attempt."""
    strategy: CorrectionStrategy
    original_query: str
    corrected_query: str
    confidence: float
    corrections_applied: List[str]
    estimated_success_rate: float

class QueryCorrectionService:
    """
    High-level service for SQL query correction and optimization.
    Integrates with the Error Recovery Engine and provides intelligent retry strategies.
    """
    
    def __init__(self, db_connection=None, strategy: CorrectionStrategy = CorrectionStrategy.MODERATE):
        self.db_connection = db_connection
        self.default_strategy = strategy
        self.recovery_engine = SQLErrorRecoveryEngine(db_connection)
        
        # Correction patterns and rules
        self.correction_rules = self._initialize_correction_rules()
        self.query_patterns = self._initialize_query_patterns()
        
        # Service statistics
        self.correction_stats = {
            "total_corrections": 0,
            "successful_corrections": 0,
            "corrections_by_strategy": {s.value: 0 for s in CorrectionStrategy},
            "common_query_issues": {},
            "performance_improvements": [],
            "last_correction": None
        }
    
    def _initialize_correction_rules(self) -> Dict[str, Any]:
        """Initialize high-level correction rules."""
        return {
            "performance_optimizations": [
                {
                    "name": "add_missing_limit",
                    "pattern": r"SELECT.*FROM.*(?!.*LIMIT)(?!.*TOP)",
                    "fix": lambda q: self._add_limit_clause(q),
                    "confidence": 0.9,
                    "description": "Add LIMIT clause to prevent large result sets"
                },
                {
                    "name": "optimize_select_star",
                    "pattern": r"SELECT\s+\*\s+FROM",
                    "fix": lambda q: self._suggest_specific_columns(q),
                    "confidence": 0.7,
                    "description": "Replace SELECT * with specific columns"
                },
                {
                    "name": "add_where_conditions",
                    "pattern": r"SELECT.*FROM\s+\w+\s*(?!WHERE)(?!JOIN)(?!LIMIT)",
                    "fix": lambda q: self._suggest_where_clause(q),
                    "confidence": 0.5,
                    "description": "Suggest WHERE clause to filter results"
                }
            ],
            "syntax_corrections": [
                {
                    "name": "fix_missing_commas",
                    "pattern": r"SELECT\s+(\w+)\s+(\w+)(?!\s*,|\s*FROM)",
                    "fix": lambda q: re.sub(r"SELECT\s+(\w+)\s+(\w+)(?=\s+FROM)", r"SELECT \1, \2", q, flags=re.IGNORECASE),
                    "confidence": 0.8,
                    "description": "Add missing commas in SELECT clause"
                },
                {
                    "name": "fix_quote_consistency",
                    "pattern": r"['\"](\d+)['\"]",
                    "fix": lambda q: re.sub(r"['\"](\d+)['\"]", r"\1", q),
                    "confidence": 0.9,
                    "description": "Remove unnecessary quotes from numeric values"
                },
                {
                    "name": "fix_case_sensitivity",
                    "pattern": r"\b(select|from|where|order by|group by|having|join|inner|left|right|full|outer)\b",
                    "fix": lambda q: self._normalize_sql_keywords(q),
                    "confidence": 0.6,
                    "description": "Normalize SQL keyword casing"
                }
            ],
            "semantic_corrections": [
                {
                    "name": "fix_aggregation_without_group_by",
                    "pattern": r"SELECT.*(?:COUNT|SUM|AVG|MAX|MIN)\s*\([^)]+\).*FROM.*(?!GROUP BY)",
                    "fix": lambda q: self._add_group_by_clause(q),
                    "confidence": 0.7,
                    "description": "Add GROUP BY clause for aggregate functions"
                },
                {
                    "name": "fix_having_without_group_by",
                    "pattern": r"SELECT.*HAVING.*(?<!GROUP BY)",
                    "fix": lambda q: self._fix_having_clause(q),
                    "confidence": 0.8,
                    "description": "Fix HAVING clause without GROUP BY"
                }
            ]
        }
    
    def _initialize_query_patterns(self) -> Dict[str, Any]:
        """Initialize common query patterns and their corrections."""
        return {
            "common_mistakes": {
                # Common typos and mistakes
                "SELCET": "SELECT",
                "FORM": "FROM", 
                "WEHRE": "WHERE",
                "GROPU BY": "GROUP BY",
                "OREDER BY": "ORDER BY",
                "HAVIN": "HAVING",
                "JION": "JOIN",
                "INNE JOIN": "INNER JOIN",
                "LEFY JOIN": "LEFT JOIN",
                "RIGH JOIN": "RIGHT JOIN",
                # Function name corrections
                "LENGHT": "LENGTH",
                "SUBSTRIN": "SUBSTRING",
                "CONCATE": "CONCAT",
                "CONUT": "COUNT",
                "SUMM": "SUM",
                "AVRAGE": "AVG",
                "MAXIMU": "MAX",
                "MINIMU": "MIN",
            },
            "operator_corrections": {
                "=<": "<=",
                "=>": ">=", 
                "!=": "<>",  # Standardize to SQL standard
                "==": "=",   # Fix programming language confusion
                "&&": "AND",
                "||": "OR",
                "!": "NOT",
            }
        }
    
    def correct_query(self, query: str, error_message: str = None, 
                     strategy: CorrectionStrategy = None) -> List[CorrectionAttempt]:
        """
        Main method to correct a SQL query with multiple strategies.
        Returns a list of correction attempts ordered by confidence.
        """
        if strategy is None:
            strategy = self.default_strategy
        
        self.correction_stats["total_corrections"] += 1
        self.correction_stats["corrections_by_strategy"][strategy.value] += 1
        
        attempts = []
        
        # If we have an error message, use the recovery engine first
        if error_message:
            recovery_result = self.recovery_engine.recover_from_error(error_message, query)
            if recovery_result.success:
                attempts.append(CorrectionAttempt(
                    strategy=strategy,
                    original_query=query,
                    corrected_query=recovery_result.corrected_query,
                    confidence=recovery_result.confidence,
                    corrections_applied=recovery_result.corrections_applied or [],
                    estimated_success_rate=recovery_result.confidence
                ))
        
        # Apply general corrections based on strategy
        if strategy == CorrectionStrategy.CONSERVATIVE:
            attempts.extend(self._apply_conservative_corrections(query))
        elif strategy == CorrectionStrategy.MODERATE:
            attempts.extend(self._apply_moderate_corrections(query))
        elif strategy == CorrectionStrategy.AGGRESSIVE:
            attempts.extend(self._apply_aggressive_corrections(query))
        
        # Sort by confidence and estimated success rate
        attempts.sort(key=lambda x: (x.confidence, x.estimated_success_rate), reverse=True)
        
        # Update statistics
        if attempts:
            self.correction_stats["successful_corrections"] += 1
            self.correction_stats["last_correction"] = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy.value,
                "attempts_count": len(attempts),
                "best_confidence": attempts[0].confidence if attempts else 0
            }
        
        return attempts
    
    def _apply_conservative_corrections(self, query: str) -> List[CorrectionAttempt]:
        """Apply only safe, high-confidence corrections."""
        attempts = []
        
        # Only apply syntax corrections with high confidence
        for rule in self.correction_rules["syntax_corrections"]:
            if rule["confidence"] >= 0.8:
                corrected = self._apply_correction_rule(query, rule)
                if corrected != query:
                    attempts.append(CorrectionAttempt(
                        strategy=CorrectionStrategy.CONSERVATIVE,
                        original_query=query,
                        corrected_query=corrected,
                        confidence=rule["confidence"],
                        corrections_applied=[rule["description"]],
                        estimated_success_rate=rule["confidence"] * 0.9
                    ))
        
        # Apply common typo fixes
        corrected_query = self._fix_common_typos(query)
        if corrected_query != query:
            attempts.append(CorrectionAttempt(
                strategy=CorrectionStrategy.CONSERVATIVE,
                original_query=query,
                corrected_query=corrected_query,
                confidence=0.95,
                corrections_applied=["Fixed common typos"],
                estimated_success_rate=0.9
            ))
        
        return attempts
    
    def _apply_moderate_corrections(self, query: str) -> List[CorrectionAttempt]:
        """Apply balanced corrections including performance optimizations."""
        attempts = self._apply_conservative_corrections(query)
        
        # Add performance optimizations
        for rule in self.correction_rules["performance_optimizations"]:
            if rule["confidence"] >= 0.7:
                if re.search(rule["pattern"], query, re.IGNORECASE):
                    corrected = rule["fix"](query)
                    if corrected != query:
                        attempts.append(CorrectionAttempt(
                            strategy=CorrectionStrategy.MODERATE,
                            original_query=query,
                            corrected_query=corrected,
                            confidence=rule["confidence"],
                            corrections_applied=[rule["description"]],
                            estimated_success_rate=rule["confidence"] * 0.8
                        ))
        
        # Add semantic corrections with moderate confidence
        for rule in self.correction_rules["semantic_corrections"]:
            if rule["confidence"] >= 0.6:
                if re.search(rule["pattern"], query, re.IGNORECASE):
                    corrected = rule["fix"](query)
                    if corrected != query:
                        attempts.append(CorrectionAttempt(
                            strategy=CorrectionStrategy.MODERATE,
                            original_query=query,
                            corrected_query=corrected,
                            confidence=rule["confidence"],
                            corrections_applied=[rule["description"]],
                            estimated_success_rate=rule["confidence"] * 0.7
                        ))
        
        return attempts
    
    def _apply_aggressive_corrections(self, query: str) -> List[CorrectionAttempt]:
        """Apply all available corrections including experimental ones."""
        attempts = self._apply_moderate_corrections(query)
        
        # Apply all remaining corrections regardless of confidence
        all_rules = (
            self.correction_rules["performance_optimizations"] +
            self.correction_rules["syntax_corrections"] +
            self.correction_rules["semantic_corrections"]
        )
        
        for rule in all_rules:
            if rule["confidence"] < 0.6:  # Only apply low-confidence rules in aggressive mode
                if re.search(rule["pattern"], query, re.IGNORECASE):
                    corrected = rule["fix"](query)
                    if corrected != query:
                        attempts.append(CorrectionAttempt(
                            strategy=CorrectionStrategy.AGGRESSIVE,
                            original_query=query,
                            corrected_query=corrected,
                            confidence=rule["confidence"],
                            corrections_applied=[rule["description"]],
                            estimated_success_rate=rule["confidence"] * 0.5
                        ))
        
        return attempts
    
    def _apply_correction_rule(self, query: str, rule: Dict[str, Any]) -> str:
        """Apply a specific correction rule to a query."""
        try:
            return rule["fix"](query)
        except Exception as e:
            logger.warning(f"Failed to apply correction rule {rule['name']}: {e}")
            return query
    
    def _fix_common_typos(self, query: str) -> str:
        """Fix common SQL typos and mistakes."""
        corrected = query
        
        # Fix common keyword typos
        for typo, correction in self.query_patterns["common_mistakes"].items():
            corrected = re.sub(rf'\b{re.escape(typo)}\b', correction, corrected, flags=re.IGNORECASE)
        
        # Fix operator typos
        for typo, correction in self.query_patterns["operator_corrections"].items():
            corrected = corrected.replace(typo, correction)
        
        return corrected
    
    def _add_limit_clause(self, query: str) -> str:
        """Add a LIMIT clause to queries that don't have one."""
        if 'LIMIT' not in query.upper() and 'TOP' not in query.upper():
            # Remove trailing semicolon if present, add LIMIT, then add semicolon back
            query = query.rstrip(';').rstrip()
            return f"{query} LIMIT 100;"
        return query
    
    def _suggest_specific_columns(self, query: str) -> str:
        """Replace SELECT * with specific columns (basic implementation)."""
        # This is a simplified version - in practice, you'd need schema information
        # For now, we'll just add a comment suggesting the improvement
        if 'SELECT *' in query.upper():
            return query.replace('SELECT *', 'SELECT id, name -- TODO: Specify actual columns needed')
        return query
    
    def _suggest_where_clause(self, query: str) -> str:
        """Suggest adding a WHERE clause to filter results."""
        # Basic heuristic: if no WHERE clause and no JOIN, suggest adding one
        if 'WHERE' not in query.upper() and 'JOIN' not in query.upper():
            # Find the FROM clause and add a comment
            from_match = re.search(r'(FROM\s+\w+)', query, re.IGNORECASE)
            if from_match:
                from_clause = from_match.group(1)
                suggested = query.replace(
                    from_clause, 
                    f"{from_clause} -- TODO: Consider adding WHERE clause for filtering"
                )
                return suggested
        return query
    
    def _normalize_sql_keywords(self, query: str) -> str:
        """Normalize SQL keyword casing to uppercase."""
        keywords = ['SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'HAVING', 
                   'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'ON', 'AS',
                   'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL']
        
        corrected = query
        for keyword in keywords:
            corrected = re.sub(rf'\b{re.escape(keyword)}\b', keyword, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def _add_group_by_clause(self, query: str) -> str:
        """Add GROUP BY clause when aggregate functions are used without it."""
        # Simple heuristic: if there are aggregate functions but no GROUP BY
        if re.search(r'\b(COUNT|SUM|AVG|MAX|MIN)\s*\(', query, re.IGNORECASE) and 'GROUP BY' not in query.upper():
            # Extract non-aggregate columns from SELECT clause
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_part = select_match.group(1)
                # This is a very basic implementation - real-world would need proper parsing
                columns = [col.strip() for col in select_part.split(',')]
                non_aggregate_cols = []
                
                for col in columns:
                    if not re.search(r'\b(COUNT|SUM|AVG|MAX|MIN)\s*\(', col, re.IGNORECASE):
                        # Remove aliases and functions
                        col_name = re.sub(r'\s+AS\s+\w+', '', col, flags=re.IGNORECASE)
                        col_name = re.sub(r'\w+\s*\(\s*([^)]+)\s*\)', r'\1', col_name)
                        if col_name.strip() and col_name.strip() != '*':
                            non_aggregate_cols.append(col_name.strip())
                
                if non_aggregate_cols:
                    group_by_clause = f" GROUP BY {', '.join(non_aggregate_cols[:3])}"  # Limit to first 3
                    # Insert before ORDER BY, HAVING, or LIMIT if they exist
                    for clause in ['ORDER BY', 'HAVING', 'LIMIT']:
                        if clause in query.upper():
                            query = re.sub(rf'\s+{clause}', f'{group_by_clause} {clause}', query, flags=re.IGNORECASE)
                            return query
                    
                    # If no other clauses, add at the end
                    query = query.rstrip(';') + group_by_clause + ';'
        
        return query
    
    def _fix_having_clause(self, query: str) -> str:
        """Fix HAVING clause that appears without GROUP BY."""
        if 'HAVING' in query.upper() and 'GROUP BY' not in query.upper():
            # Convert HAVING to WHERE if no aggregation is involved
            having_match = re.search(r'HAVING\s+(.*?)(?:\s+ORDER|\s+LIMIT|$)', query, re.IGNORECASE)
            if having_match:
                having_condition = having_match.group(1)
                # If the HAVING condition doesn't involve aggregate functions, convert to WHERE
                if not re.search(r'\b(COUNT|SUM|AVG|MAX|MIN)\s*\(', having_condition, re.IGNORECASE):
                    query = re.sub(r'\s+HAVING\s+', ' WHERE ', query, flags=re.IGNORECASE)
        
        return query
    
    def get_correction_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Get correction suggestions without applying them."""
        suggestions = []
        
        # Check all correction rules
        all_rules = (
            self.correction_rules["performance_optimizations"] +
            self.correction_rules["syntax_corrections"] +
            self.correction_rules["semantic_corrections"]
        )
        
        for rule in all_rules:
            if re.search(rule["pattern"], query, re.IGNORECASE):
                suggestions.append({
                    "type": rule["name"],
                    "description": rule["description"],
                    "confidence": rule["confidence"],
                    "severity": "high" if rule["confidence"] > 0.8 else "medium" if rule["confidence"] > 0.6 else "low"
                })
        
        # Check for common typos
        typos_found = []
        for typo in self.query_patterns["common_mistakes"]:
            if re.search(rf'\b{re.escape(typo)}\b', query, re.IGNORECASE):
                typos_found.append(typo)
        
        if typos_found:
            suggestions.append({
                "type": "typo_correction",
                "description": f"Found potential typos: {', '.join(typos_found)}",
                "confidence": 0.9,
                "severity": "high"
            })
        
        return suggestions
    
    def get_correction_stats(self) -> Dict[str, Any]:
        """Get comprehensive correction statistics."""
        total_corrections = self.correction_stats["total_corrections"]
        successful_corrections = self.correction_stats["successful_corrections"]
        
        recovery_stats = self.recovery_engine.get_recovery_stats()
        
        return {
            **self.correction_stats,
            "success_rate": (successful_corrections / max(total_corrections, 1)) * 100,
            "recovery_engine_stats": recovery_stats,
            "combined_success_rate": (
                (successful_corrections + recovery_stats["successful_recoveries"]) / 
                max(total_corrections + recovery_stats["total_errors"], 1)
            ) * 100
        }
    
    def reset_stats(self):
        """Reset correction statistics."""
        self.correction_stats = {
            "total_corrections": 0,
            "successful_corrections": 0,
            "corrections_by_strategy": {s.value: 0 for s in CorrectionStrategy},
            "common_query_issues": {},
            "performance_improvements": [],
            "last_correction": None
        }
        self.recovery_engine.reset_stats()
        logger.info("Query correction statistics reset.")



