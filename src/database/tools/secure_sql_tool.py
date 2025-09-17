#!/usr/bin/env python3
"""
Secure SQL Tool Module
Enhanced security tool that builds on the existing CustomQuerySQLDatabaseTool
with comprehensive SQL injection prevention and security validation.
"""

import re
import time
import hashlib
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime

# Import your existing custom tool
from .custom_sql_tool import CustomQuerySQLDatabaseTool
from langchain_core.tools import BaseTool
from langchain_community.utilities import SQLDatabase
from pydantic import Field


class SecurityViolation(Exception):
    """Custom exception for security violations."""
    
    def __init__(self, message: str, violation_type: str, risk_level: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.violation_type = violation_type
        self.risk_level = risk_level
        self.details = details or {}


class SecureUniversalSQLTool(CustomQuerySQLDatabaseTool):
    """
    Enhanced SQL tool with comprehensive security validation.
    Builds on your existing CustomQuerySQLDatabaseTool while adding advanced security features.
    """
    
    name: str = "sql_db_query_secure"
    description: str = """
    Execute a SQL query against the database with enhanced security validation.
    This tool prevents SQL injection attacks and enforces security policies.
    If the query is not correct or violates security policies, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    
    # Security configuration - these will be set in __init__ to avoid Pydantic issues
    max_query_length: int = 5000
    require_limit: bool = True
    max_limit_value: int = 1000
    enable_query_logging: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize security configuration (avoid Pydantic field issues)
        self._max_query_length = getattr(self, 'max_query_length', 5000)
        self._require_limit = getattr(self, 'require_limit', True)
        self._max_limit_value = getattr(self, 'max_limit_value', 1000)
        self._enable_query_logging = getattr(self, 'enable_query_logging', True)
        
        # Security rules configuration
        self._security_rules = self._initialize_security_rules()
        
        # Initialize SQL injection detector
        try:
            from .sql_injection_patterns import SQLInjectionDetector
            self._injection_detector = SQLInjectionDetector()
        except ImportError:
            print("⚠️ SQL injection detector not available")
            self._injection_detector = None
        
        # Security statistics
        self._security_stats = {
            "total_queries": 0,
            "blocked_queries": 0,
            "violations_by_type": {},
            "last_violation": None
        }
        
        # Query cache for performance (integrates with your existing performance monitoring)
        self._query_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    def _initialize_security_rules(self) -> Dict[str, Any]:
        """Initialize comprehensive security rules."""
        return {
            # High-risk patterns that should be completely blocked
            "critical_violations": [
                {
                    "pattern": r';\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|REPLACE)\s+',
                    "description": "DML/DDL operations not allowed",
                    "risk_level": "critical"
                },
                {
                    "pattern": r'UNION\s+(?:ALL\s+)?SELECT.*(?:--|\#|\/\*)',
                    "description": "SQL injection attempt via UNION with comments",
                    "risk_level": "critical"
                },
                {
                    "pattern": r'(EXEC|EXECUTE|EVAL)\s*\(',
                    "description": "Code execution functions not allowed",
                    "risk_level": "critical"
                },
                {
                    "pattern": r'(xp_|sp_)\w+',
                    "description": "SQL Server extended/stored procedures not allowed",
                    "risk_level": "critical"
                },
                {
                    "pattern": r'(LOAD_FILE|INTO\s+(?:OUTFILE|DUMPFILE)|LOAD\s+DATA)',
                    "description": "File system operations not allowed",
                    "risk_level": "critical"
                },
                {
                    "pattern": r'(OPENROWSET|OPENDATASOURCE|OPENXML)',
                    "description": "External data access functions not allowed",
                    "risk_level": "critical"
                }
            ],
            
            # Medium-risk patterns that need validation
            "medium_violations": [
                {
                    "pattern": r'\/\*.*?\*\/|--.*$',
                    "description": "SQL comments detected (potential obfuscation)",
                    "risk_level": "medium"
                },
                {
                    "pattern": r'UNION\s+(?:ALL\s+)?SELECT',
                    "description": "UNION operations require careful review",
                    "risk_level": "medium"
                },
                {
                    "pattern": r'(CONCAT|GROUP_CONCAT|STRING_AGG)\s*\([^)]*SELECT',
                    "description": "Nested SELECT in string functions",
                    "risk_level": "medium"
                },
                {
                    "pattern": r'(SLEEP|WAITFOR|BENCHMARK)\s*\(',
                    "description": "Time-based functions (potential DoS)",
                    "risk_level": "medium"
                }
            ],
            
            # Performance and best practice violations
            "performance_violations": [
                {
                    "pattern": r'SELECT\s+\*\s+FROM\s+\w+(?:\s+(?:JOIN|WHERE|GROUP|ORDER|HAVING|LIMIT))?$',
                    "description": "SELECT * without specific column selection",
                    "risk_level": "low"
                },
                {
                    "pattern": r'WHERE\s+[^=<>!]*\s*=\s*[^=<>!]*\s+OR\s+1\s*=\s*1',
                    "description": "Always-true conditions (potential injection)",
                    "risk_level": "high"
                }
            ],
            
            # Suspicious functions that need monitoring
            "suspicious_functions": [
                'CHAR', 'CHR', 'ASCII', 'UNHEX', 'HEX',
                'LOAD_FILE', 'FILE_PRIV', 'DUMPFILE',
                'SCRIPT', 'SHELL', 'SYSTEM',
                'BENCHMARK', 'SLEEP', 'WAITFOR',
                'USER', 'DATABASE', 'VERSION', 'CONNECTION_ID'
            ],
            
            # Required security constraints
            "required_constraints": {
                "max_query_length": 5000,
                "require_limit_for_select": True,
                "max_limit_value": 1000,
                "max_joins": 5,
                "max_subqueries": 3
            }
        }
    
    def _validate_query_security(self, sql: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Comprehensive security validation with detailed reporting.
        
        Returns:
            Tuple of (is_safe, message, security_details)
        """
        security_report = {
            "is_safe": True,
            "violations": [],
            "warnings": [],
            "risk_level": "low",
            "recommendations": [],
            "query_hash": hashlib.md5(sql.encode()).hexdigest()[:8],
            "timestamp": datetime.now().isoformat()
        }
        
        sql_normalized = sql.strip()
        sql_upper = sql_normalized.upper()
        
        try:
            # 1. Basic validation
            if not sql_normalized:
                security_report["violations"].append("Empty query not allowed")
                security_report["is_safe"] = False
                return False, "Empty query", security_report
            
            # 2. Advanced injection detection using SQLInjectionDetector
            if self._injection_detector:
                injection_report = self._injection_detector.generate_security_report(sql_normalized)
                if not injection_report["safe_to_execute"]:
                    security_report["violations"].extend([
                        f"SQL injection pattern detected: {pattern['description']}"
                        for pattern in injection_report["detailed_patterns"]
                        if pattern["risk_level"] in ["critical", "high"]
                    ])
                    security_report["risk_level"] = injection_report["risk_level"]
                    security_report["is_safe"] = False
                
                # Add warnings for medium/low risk patterns
                medium_low_patterns = [
                    pattern for pattern in injection_report["detailed_patterns"]
                    if pattern["risk_level"] in ["medium", "low"]
                ]
                for pattern in medium_low_patterns:
                    security_report["warnings"].append(f"Potential issue: {pattern['description']}")
            
            # 3. Length validation
            if len(sql_normalized) > self._security_rules["required_constraints"]["max_query_length"]:
                security_report["violations"].append(f"Query length exceeds {self._max_query_length} characters")
                security_report["risk_level"] = "medium"
                security_report["is_safe"] = False
            
            # 4. Check critical violations (auto-block)
            for rule in self._security_rules["critical_violations"]:
                if re.search(rule["pattern"], sql_normalized, re.IGNORECASE | re.MULTILINE):
                    security_report["violations"].append(rule["description"])
                    security_report["risk_level"] = "critical"
                    security_report["is_safe"] = False
            
            # 5. Check medium-risk violations
            for rule in self._security_rules["medium_violations"]:
                if re.search(rule["pattern"], sql_normalized, re.IGNORECASE | re.MULTILINE):
                    if rule["risk_level"] == "high":
                        security_report["violations"].append(rule["description"])
                        security_report["is_safe"] = False
                    else:
                        security_report["warnings"].append(rule["description"])
                    
                    if security_report["risk_level"] == "low":
                        security_report["risk_level"] = rule["risk_level"]
            
            # 6. Check performance violations
            for rule in self._security_rules["performance_violations"]:
                if re.search(rule["pattern"], sql_normalized, re.IGNORECASE | re.MULTILINE):
                    if rule["risk_level"] == "high":
                        security_report["violations"].append(rule["description"])
                        security_report["is_safe"] = False
                    else:
                        security_report["warnings"].append(rule["description"])
                        security_report["recommendations"].append("Consider optimizing query performance")
            
            # 7. Check for suspicious functions
            suspicious_found = []
            for func in self._security_rules["suspicious_functions"]:
                if re.search(rf'\b{func}\s*\(', sql_upper):
                    suspicious_found.append(func)
            
            if suspicious_found:
                security_report["warnings"].append(f"Suspicious functions detected: {', '.join(suspicious_found)}")
                if len(suspicious_found) > 2:
                    security_report["risk_level"] = "medium"
            
            # 8. Validate LIMIT requirement for SELECT queries
            if (self._require_limit and 
                sql_upper.strip().startswith('SELECT') and 
                'LIMIT' not in sql_upper and 
                'TOP' not in sql_upper):
                
                security_report["violations"].append("SELECT queries must include LIMIT clause")
                security_report["recommendations"].append("Add LIMIT clause to prevent excessive resource usage")
                security_report["is_safe"] = False
            
            # 9. Validate LIMIT value if present
            limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
            if limit_match:
                limit_value = int(limit_match.group(1))
                if limit_value > self._max_limit_value:
                    security_report["violations"].append(f"LIMIT value {limit_value} exceeds maximum allowed {self._max_limit_value}")
                    security_report["is_safe"] = False
            
            # 10. Check for excessive complexity
            join_count = len(re.findall(r'\bJOIN\b', sql_upper))
            if join_count > self._security_rules["required_constraints"]["max_joins"]:
                security_report["warnings"].append(f"Query has {join_count} JOINs (max recommended: {self._security_rules['required_constraints']['max_joins']})")
                security_report["recommendations"].append("Consider breaking complex queries into smaller parts")
            
            # 11. Check for nested subqueries
            subquery_count = sql_normalized.count('(') - sql_normalized.count(')')
            if abs(subquery_count) > self._security_rules["required_constraints"]["max_subqueries"]:
                security_report["warnings"].append("Complex nested subqueries detected")
                security_report["recommendations"].append("Consider simplifying query structure")
            
            # Final risk assessment
            if security_report["violations"]:
                security_report["is_safe"] = False
                if not security_report["risk_level"] or security_report["risk_level"] == "low":
                    security_report["risk_level"] = "medium"
            
        except Exception as e:
            security_report["violations"].append(f"Security validation error: {str(e)}")
            security_report["is_safe"] = False
            security_report["risk_level"] = "critical"
        
        # Generate summary message
        if security_report["is_safe"]:
            message = "Security validation passed"
            if security_report["warnings"]:
                message += f" (with {len(security_report['warnings'])} warnings)"
        else:
            message = f"Security validation failed: {len(security_report['violations'])} violations detected"
        
        return security_report["is_safe"], message, security_report
    
    def _log_security_event(self, query: str, security_report: Dict[str, Any], execution_result: str = None):
        """Log security events for monitoring and analysis."""
        if not self._enable_query_logging:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_hash": security_report.get("query_hash", "unknown"),
            "query_preview": query[:100] + "..." if len(query) > 100 else query,
            "risk_level": security_report.get("risk_level", "unknown"),
            "violations": security_report.get("violations", []),
            "warnings": security_report.get("warnings", []),
            "blocked": not security_report.get("is_safe", True),
            "execution_success": execution_result and not execution_result.startswith("Error:")
        }
        
        # Update statistics
        self._security_stats["total_queries"] += 1
        if not security_report.get("is_safe", True):
            self._security_stats["blocked_queries"] += 1
            self._security_stats["last_violation"] = log_entry
            
            # Count violations by type
            for violation in security_report.get("violations", []):
                violation_key = violation.split(":")[0] if ":" in violation else violation
                self._security_stats["violations_by_type"][violation_key] = \
                    self._security_stats["violations_by_type"].get(violation_key, 0) + 1
        
        # Print security log (integrates with your existing logging)
        if security_report.get("risk_level") in ["critical", "high"]:
            print(f"🚨 SECURITY ALERT [{security_report['risk_level'].upper()}]: {log_entry['query_preview']}")
            for violation in security_report.get("violations", []):
                print(f"   ⚠️ {violation}")
        elif security_report.get("warnings"):
            print(f"⚠️ Security warnings for query {security_report.get('query_hash', 'unknown')}: {len(security_report['warnings'])} warnings")
    
    def _run(self, query: str, run_manager: Optional[Any] = None) -> str:
        """
        Enhanced execution with comprehensive security validation.
        Builds on your existing _clean_sql_query method.
        """
        start_time = time.time()
        
        try:
            # 1. Clean the SQL query (your existing functionality)
            cleaned_query = self._clean_sql_query(query)
            
            # 2. Security validation
            is_safe, security_message, security_report = self._validate_query_security(cleaned_query)
            
            if not is_safe:
                # Log security violation
                self._log_security_event(cleaned_query, security_report, "BLOCKED")
                
                # Return detailed security error
                error_details = []
                for violation in security_report.get("violations", []):
                    error_details.append(f"• {violation}")
                
                recommendations = security_report.get("recommendations", [])
                if recommendations:
                    error_details.append("\nRecommendations:")
                    for rec in recommendations[:3]:  # Limit to top 3 recommendations
                        error_details.append(f"• {rec}")
                
                return f"Security Error: Query blocked due to security violations.\n\nViolations:\n" + "\n".join(error_details)
            
            # 3. Execute the cleaned and validated query (your existing functionality)
            print(f"🛡️ Security validation passed for query {security_report.get('query_hash', 'unknown')}")
            if security_report.get("warnings"):
                print(f"⚠️ Note: {len(security_report['warnings'])} security warnings - see recommendations")
            
            result = self.db.run(cleaned_query)
            
            # 4. Log successful execution
            self._log_security_event(cleaned_query, security_report, result)
            
            # 5. Add security metadata to result (for integration with your response formatter)
            execution_time = time.time() - start_time
            if hasattr(result, '__dict__'):
                result.security_metadata = {
                    "validation_passed": True,
                    "risk_level": security_report.get("risk_level", "low"),
                    "warnings_count": len(security_report.get("warnings", [])),
                    "execution_time": execution_time,
                    "query_hash": security_report.get("query_hash")
                }
            
            return result
            
        except Exception as e:
            # Log execution error
            error_report = {"is_safe": True, "violations": [], "warnings": [f"Execution error: {str(e)}"]}
            self._log_security_event(query, error_report, f"Error: {str(e)}")
            
            return f"Error: {e}"
    
    async def _arun(self, query: str, run_manager: Optional[Any] = None) -> str:
        """Execute the query asynchronously with security validation."""
        return self._run(query, run_manager)
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics for monitoring."""
        return {
            **self._security_stats,
            "block_rate": (self._security_stats["blocked_queries"] / 
                          max(self._security_stats["total_queries"], 1)) * 100,
            "top_violations": dict(sorted(
                self._security_stats["violations_by_type"].items(),
                key=lambda x: x[1], reverse=True
            )[:5])
        }
    
    def reset_security_stats(self):
        """Reset security statistics."""
        self._security_stats = {
            "total_queries": 0,
            "blocked_queries": 0,
            "violations_by_type": {},
            "last_violation": None
        }
