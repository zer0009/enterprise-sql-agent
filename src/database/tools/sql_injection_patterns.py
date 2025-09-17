#!/usr/bin/env python3
"""
SQL Injection Prevention Patterns
Comprehensive patterns for detecting and preventing SQL injection attacks.
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class SecurityPattern:
    """Security pattern definition."""
    pattern: str
    description: str
    risk_level: str
    category: str
    recommendation: str = ""


class SQLInjectionDetector:
    """Advanced SQL injection detection with comprehensive patterns."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.whitelist_patterns = self._initialize_whitelist()
    
    def _initialize_patterns(self) -> Dict[str, List[SecurityPattern]]:
        """Initialize comprehensive SQL injection patterns."""
        return {
            # Classic SQL Injection Patterns
            "classic_injection": [
                SecurityPattern(
                    pattern=r"(?:OR|AND)\s+(?:'1'\s*=\s*'1'|1\s*=\s*1|'a'\s*=\s*'a')",
                    description="Classic tautology-based SQL injection",
                    risk_level="critical",
                    category="injection",
                    recommendation="Use parameterized queries instead of string concatenation"
                ),
                SecurityPattern(
                    pattern=r"'\s*(?:OR|AND)\s+\w+\s*(?:LIKE|=)\s*'%",
                    description="Wildcard injection pattern",
                    risk_level="high",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"(?:^|;|\s)(?:DROP|DELETE|UPDATE|INSERT|ALTER|CREATE)\s+",
                    description="Statement termination with dangerous command",
                    risk_level="critical",
                    category="injection"
                )
            ],
            
            # Union-based Injection
            "union_injection": [
                SecurityPattern(
                    pattern=r"UNION\s+(?:ALL\s+)?SELECT",
                    description="UNION-based SQL injection attempt",
                    risk_level="critical",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"UNION\s+(?:ALL\s+)?SELECT.*(?:--|\#|\/\*)",
                    description="UNION injection with comment obfuscation",
                    risk_level="critical",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"'\s*UNION\s+SELECT\s+(?:CONCAT|GROUP_CONCAT)",
                    description="UNION injection with string concatenation",
                    risk_level="critical",
                    category="injection"
                )
            ],
            
            # Boolean-based Blind Injection
            "blind_injection": [
                SecurityPattern(
                    pattern=r"(?:AND|OR)\s+\d+\s*[<>=!]+\s*\d+",
                    description="Boolean-based blind SQL injection",
                    risk_level="high",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"(?:AND|OR)\s+(?:ASCII|ORD|CHAR)\s*\(",
                    description="Character-based blind injection",
                    risk_level="high",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"(?:AND|OR)\s+(?:LENGTH|LEN|CHAR_LENGTH)\s*\(",
                    description="Length-based blind injection",
                    risk_level="high",
                    category="injection"
                )
            ],
            
            # Time-based Injection
            "time_injection": [
                SecurityPattern(
                    pattern=r"(?:SLEEP|WAITFOR|BENCHMARK|pg_sleep)\s*\(\s*\d+",
                    description="Time-based SQL injection",
                    risk_level="critical",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"IF\s*\([^)]*,\s*(?:SLEEP|WAITFOR|BENCHMARK)",
                    description="Conditional time-based injection",
                    risk_level="critical",
                    category="injection"
                )
            ],
            
            # Error-based Injection
            "error_injection": [
                SecurityPattern(
                    pattern=r"(?:AND|OR)\s+(?:EXTRACTVALUE|UPDATEXML)\s*\(",
                    description="XML function-based error injection",
                    risk_level="high",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"(?:AND|OR)\s+(?:EXP|FLOOR|RAND)\s*\([^)]*\)",
                    description="Mathematical function-based error injection",
                    risk_level="high",
                    category="injection"
                ),
                SecurityPattern(
                    pattern=r"CAST\s*\([^)]*AS\s+(?:INT|INTEGER|DECIMAL)\s*\)",
                    description="Type casting error injection",
                    risk_level="medium",
                    category="injection"
                )
            ],
            
            # Second-order Injection
            "second_order": [
                SecurityPattern(
                    pattern=r"(?:INSERT|UPDATE).*VALUES.*(?:CONCAT|CHR|CHAR)\s*\(",
                    description="Potential second-order injection via data insertion",
                    risk_level="medium",
                    category="injection"
                )
            ],
            
            # NoSQL Injection Patterns
            "nosql_injection": [
                SecurityPattern(
                    pattern=r"\$(?:ne|gt|lt|gte|lte|in|nin|regex|where)",
                    description="MongoDB operator injection",
                    risk_level="high",
                    category="nosql_injection"
                ),
                SecurityPattern(
                    pattern=r"(?:this\.|function\s*\()",
                    description="JavaScript injection in NoSQL",
                    risk_level="high",
                    category="nosql_injection"
                )
            ],
            
            # Code Execution Attempts
            "code_execution": [
                SecurityPattern(
                    pattern=r"(?:EXEC|EXECUTE|EVAL)\s*\(",
                    description="Code execution function",
                    risk_level="critical",
                    category="execution"
                ),
                SecurityPattern(
                    pattern=r"(?:xp_|sp_)\w+",
                    description="SQL Server extended/stored procedure",
                    risk_level="critical",
                    category="execution"
                ),
                SecurityPattern(
                    pattern=r"(?:OPENROWSET|OPENDATASOURCE|OPENXML|BULK)",
                    description="External data access function",
                    risk_level="critical",
                    category="execution"
                )
            ],
            
            # File System Access
            "file_access": [
                SecurityPattern(
                    pattern=r"(?:LOAD_FILE|INTO\s+(?:OUTFILE|DUMPFILE)|LOAD\s+DATA)",
                    description="File system access function",
                    risk_level="critical",
                    category="file_access"
                ),
                SecurityPattern(
                    pattern=r"(?:FILE_PRIV|FILE_PRIVILEGES)",
                    description="File privilege check",
                    risk_level="high",
                    category="file_access"
                )
            ],
            
            # Information Disclosure
            "info_disclosure": [
                SecurityPattern(
                    pattern=r"(?:@@|GLOBAL\.|SESSION\.)\w+",
                    description="System variable access",
                    risk_level="medium",
                    category="disclosure"
                ),
                SecurityPattern(
                    pattern=r"(?:USER|CURRENT_USER|SESSION_USER|SYSTEM_USER)\s*\(\s*\)",
                    description="User information function",
                    risk_level="low",
                    category="disclosure"
                ),
                SecurityPattern(
                    pattern=r"(?:DATABASE|SCHEMA|VERSION|CONNECTION_ID)\s*\(\s*\)",
                    description="Database information function",
                    risk_level="low",
                    category="disclosure"
                )
            ],
            
            # Comment-based Obfuscation
            "obfuscation": [
                SecurityPattern(
                    pattern=r"\/\*.*?\*\/",
                    description="Block comment (potential obfuscation)",
                    risk_level="medium",
                    category="obfuscation"
                ),
                SecurityPattern(
                    pattern=r"--.*$",
                    description="Line comment (potential obfuscation)",
                    risk_level="low",
                    category="obfuscation"
                ),
                SecurityPattern(
                    pattern=r"\#.*$",
                    description="Hash comment (MySQL)",
                    risk_level="low",
                    category="obfuscation"
                )
            ],
            
            # Encoding-based Evasion
            "encoding_evasion": [
                SecurityPattern(
                    pattern=r"(?:0x[0-9a-fA-F]+|UNHEX\s*\(|HEX\s*\()",
                    description="Hexadecimal encoding",
                    risk_level="medium",
                    category="evasion"
                ),
                SecurityPattern(
                    pattern=r"(?:CHAR|CHR|ASCII)\s*\(\s*\d+",
                    description="Character code encoding",
                    risk_level="medium",
                    category="evasion"
                ),
                SecurityPattern(
                    pattern=r"(?:CONVERT|CAST)\s*\([^)]*USING\s+\w+",
                    description="Character set conversion",
                    risk_level="low",
                    category="evasion"
                )
            ]
        }
    
    def _initialize_whitelist(self) -> List[str]:
        """Initialize patterns that are typically safe."""
        return [
            r"^SELECT\s+(?:DISTINCT\s+)?[\w\s,\.\(\)]+\s+FROM\s+\w+(?:\s+WHERE\s+[\w\s=<>!',\.\(\)]+)?(?:\s+GROUP\s+BY\s+[\w\s,]+)?(?:\s+ORDER\s+BY\s+[\w\s,]+)?(?:\s+LIMIT\s+\d+)?;?$",
            r"^DESCRIBE\s+\w+;?$",
            r"^SHOW\s+(?:TABLES|COLUMNS|INDEX);?$",
            r"^EXPLAIN\s+SELECT\s+.*$"
        ]
    
    def detect_injection_patterns(self, query: str) -> List[Dict[str, Any]]:
        """
        Detect SQL injection patterns in a query.
        
        Returns:
            List of detected patterns with details
        """
        detected_patterns = []
        query_normalized = query.strip()
        
        # Check each category of patterns
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern.pattern, query_normalized, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    detected_patterns.append({
                        "category": category,
                        "pattern": pattern.pattern,
                        "description": pattern.description,
                        "risk_level": pattern.risk_level,
                        "match": match.group(0),
                        "position": match.span(),
                        "recommendation": pattern.recommendation
                    })
        
        return detected_patterns
    
    def is_whitelisted(self, query: str) -> bool:
        """Check if query matches safe whitelist patterns."""
        query_normalized = query.strip()
        
        for pattern in self.whitelist_patterns:
            if re.match(pattern, query_normalized, re.IGNORECASE):
                return True
        
        return False
    
    def calculate_risk_score(self, detected_patterns: List[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Calculate overall risk score for a query.
        
        Returns:
            Tuple of (risk_score, risk_level)
        """
        if not detected_patterns:
            return 0, "safe"
        
        risk_scores = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25
        }
        
        total_score = 0
        max_risk_level = "safe"
        
        for pattern in detected_patterns:
            risk_level = pattern["risk_level"]
            score = risk_scores.get(risk_level, 0)
            total_score += score
            
            # Track highest risk level
            if risk_level == "critical":
                max_risk_level = "critical"
            elif risk_level == "high" and max_risk_level not in ["critical"]:
                max_risk_level = "high"
            elif risk_level == "medium" and max_risk_level not in ["critical", "high"]:
                max_risk_level = "medium"
            elif risk_level == "low" and max_risk_level == "safe":
                max_risk_level = "low"
        
        # Cap the score at 100
        final_score = min(total_score, 100)
        
        return final_score, max_risk_level
    
    def generate_security_report(self, query: str) -> Dict[str, Any]:
        """Generate comprehensive security report for a query."""
        detected_patterns = self.detect_injection_patterns(query)
        risk_score, risk_level = self.calculate_risk_score(detected_patterns)
        is_whitelisted = self.is_whitelisted(query)
        
        # Group patterns by category
        patterns_by_category = {}
        for pattern in detected_patterns:
            category = pattern["category"]
            if category not in patterns_by_category:
                patterns_by_category[category] = []
            patterns_by_category[category].append(pattern)
        
        # Generate recommendations
        recommendations = []
        if detected_patterns:
            recommendations.append("Review query for potential security vulnerabilities")
            
            if any(p["risk_level"] in ["critical", "high"] for p in detected_patterns):
                recommendations.append("Consider using parameterized queries or prepared statements")
            
            if "injection" in patterns_by_category:
                recommendations.append("Validate and sanitize all user inputs")
            
            if "obfuscation" in patterns_by_category:
                recommendations.append("Remove unnecessary comments that might hide malicious code")
        
        return {
            "query_preview": query[:100] + "..." if len(query) > 100 else query,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_whitelisted": is_whitelisted,
            "patterns_detected": len(detected_patterns),
            "patterns_by_category": patterns_by_category,
            "detailed_patterns": detected_patterns,
            "recommendations": recommendations,
            "safe_to_execute": risk_score < 75 and not any(
                p["risk_level"] == "critical" for p in detected_patterns
            )
        }


# Utility functions for integration
def quick_injection_check(query: str) -> bool:
    """Quick check for common injection patterns."""
    detector = SQLInjectionDetector()
    detected = detector.detect_injection_patterns(query)
    critical_patterns = [p for p in detected if p["risk_level"] == "critical"]
    return len(critical_patterns) == 0


def get_injection_summary(query: str) -> str:
    """Get a summary of injection risks for logging."""
    detector = SQLInjectionDetector()
    report = detector.generate_security_report(query)
    
    if report["risk_score"] == 0:
        return "No security risks detected"
    
    return f"Risk Level: {report['risk_level'].upper()} (Score: {report['risk_score']}/100), Patterns: {report['patterns_detected']}"
