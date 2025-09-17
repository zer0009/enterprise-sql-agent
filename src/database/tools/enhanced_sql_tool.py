#!/usr/bin/env python3
"""
Enhanced SQL Tool with Security and Error Recovery
Combines the SecureUniversalSQLTool with advanced error recovery capabilities.
"""

import time
import logging
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime

from .secure_sql_tool import SecureUniversalSQLTool
from .sql_error_recovery import SQLErrorRecoveryEngine
from .query_correction_service import QueryCorrectionService, CorrectionStrategy

logger = logging.getLogger(__name__)

class EnhancedUniversalSQLTool(SecureUniversalSQLTool):
    """
    Enhanced SQL tool that combines security validation with intelligent error recovery.
    
    Features:
    - All security features from SecureUniversalSQLTool
    - Automatic error detection and recovery
    - Progressive retry strategies
    - Query optimization suggestions
    - Comprehensive monitoring and analytics
    """
    
    name: str = "sql_db_query_enhanced"
    description: str = """
    Execute a SQL query against the database with enhanced security validation and automatic error recovery.
    This tool includes:
    - Advanced security checks to prevent SQL injection
    - Automatic error detection and correction
    - Progressive retry strategies for failed queries
    - Query optimization suggestions
    - Comprehensive logging and monitoring
    
    If a query fails, the tool will attempt to automatically correct common issues and retry.
    If automatic correction fails, detailed suggestions will be provided.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize error recovery components
        self._error_recovery_engine = SQLErrorRecoveryEngine(self.db)
        self._correction_service = QueryCorrectionService(self.db, CorrectionStrategy.MODERATE)
        
        # Enhanced statistics
        self._enhanced_stats = {
            "queries_with_errors": 0,
            "queries_auto_corrected": 0,
            "retry_attempts": 0,
            "successful_retries": 0,
            "correction_strategies_used": {s.value: 0 for s in CorrectionStrategy},
            "error_types_encountered": {},
            "performance_improvements": 0,
            "last_error_recovery": None
        }
        
        # Configuration
        self._max_retry_attempts = 3
        self._enable_auto_correction = True
        self._enable_progressive_strategies = True
        self._correction_confidence_threshold = 0.6
        
        logger.info("🚀 Enhanced Universal SQL Tool initialized with error recovery capabilities")
    
    def _run(self, query: str, run_manager: Optional[Any] = None) -> str:
        """Execute query with security validation and error recovery."""
        start_time = time.time()
        original_query = query
        
        # Update statistics
        self._security_stats["total_queries"] += 1
        
        # Step 1: Security validation (from parent class)
        is_safe, security_message, security_details = self._validate_query_security(query)
        
        # Log security validation
        if self._enable_query_logging and hasattr(self, 'security_monitor'):
            if hasattr(self, 'security_monitor') and self.security_monitor:
                self.security_monitor.log_query_event(
                    query=query,
                    is_safe=is_safe,
                    risk_level=security_details["risk_level"],
                    violations=security_details["violations"],
                    warnings=security_details["warnings"]
                )
        
        if not is_safe:
            self._security_stats["blocked_queries"] += 1
            error_msg = f"Security Error: {security_message}. Details: {', '.join(security_details['violations'] + security_details['warnings'])}"
            logger.warning(f"🚨 Query blocked by security validation: {error_msg}")
            return error_msg
        
        # Step 2: Clean the query
        cleaned_query = self._clean_sql_query(query)
        current_query = cleaned_query
        
        # Step 3: Execute with error recovery
        for attempt in range(self._max_retry_attempts + 1):
            try:
                logger.debug(f"🔄 Attempt {attempt + 1}/{self._max_retry_attempts + 1}: Executing query")
                
                # Execute the query
                result = self.db.run(current_query)
                
                # Success! Log the result
                execution_time = time.time() - start_time
                self._log_successful_execution(original_query, current_query, result, attempt, execution_time)
                
                return result
                
            except Exception as e:
                error_message = str(e)
                logger.warning(f"⚠️ Query execution failed (attempt {attempt + 1}): {error_message}")
                
                # Update error statistics
                self._enhanced_stats["queries_with_errors"] += 1
                if attempt > 0:
                    self._enhanced_stats["retry_attempts"] += 1
                
                # If this is the last attempt, return the error
                if attempt >= self._max_retry_attempts:
                    execution_time = time.time() - start_time
                    return self._handle_final_error(original_query, current_query, error_message, attempt, execution_time)
                
                # Attempt error recovery
                if self._enable_auto_correction:
                    recovery_result = self._attempt_error_recovery(current_query, error_message, attempt)
                    
                    if recovery_result and recovery_result.success:
                        current_query = recovery_result.corrected_query
                        self._enhanced_stats["queries_auto_corrected"] += 1
                        logger.info(f"✅ Query auto-corrected: {', '.join(recovery_result.corrections_applied)}")
                        continue
                
                # If auto-correction failed, try progressive strategies
                if self._enable_progressive_strategies and attempt < self._max_retry_attempts:
                    strategy = self._get_progressive_strategy(attempt)
                    corrected_query = self._apply_progressive_strategy(current_query, strategy, error_message)
                    
                    if corrected_query != current_query:
                        current_query = corrected_query
                        self._enhanced_stats["correction_strategies_used"][strategy.value] += 1
                        logger.info(f"🔧 Applied {strategy.value} correction strategy")
                        continue
                
                # If we reach here, we couldn't auto-correct, so we'll try the next attempt with the same query
                logger.warning(f"❌ Could not auto-correct query, attempting retry {attempt + 2}")
        
        # This should never be reached due to the loop logic, but just in case
        execution_time = time.time() - start_time
        return self._handle_final_error(original_query, current_query, "Max retries exceeded", self._max_retry_attempts, execution_time)
    
    def _attempt_error_recovery(self, query: str, error_message: str, attempt: int) -> Optional[Any]:
        """Attempt to recover from an error using the error recovery engine."""
        try:
            # Use error recovery engine
            recovery_result = self._error_recovery_engine.recover_from_error(error_message, query)
            
            if recovery_result.success:
                logger.info(f"🛠️ Error recovery successful: {recovery_result.error_type.value}")
                
                # Update statistics
                error_type = recovery_result.error_type.value
                self._enhanced_stats["error_types_encountered"][error_type] = \
                    self._enhanced_stats["error_types_encountered"].get(error_type, 0) + 1
                
                return recovery_result
            else:
                logger.debug(f"🔍 Error recovery engine could not fix: {recovery_result.suggestion}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in recovery engine: {e}")
            return None
    
    def _get_progressive_strategy(self, attempt: int) -> CorrectionStrategy:
        """Get progressively more aggressive correction strategies."""
        if attempt == 0:
            return CorrectionStrategy.CONSERVATIVE
        elif attempt == 1:
            return CorrectionStrategy.MODERATE
        else:
            return CorrectionStrategy.AGGRESSIVE
    
    def _apply_progressive_strategy(self, query: str, strategy: CorrectionStrategy, error_message: str) -> str:
        """Apply a progressive correction strategy."""
        try:
            correction_attempts = self._correction_service.correct_query(query, error_message, strategy)
            
            # Return the best correction attempt above confidence threshold
            for attempt in correction_attempts:
                if attempt.confidence >= self._correction_confidence_threshold:
                    logger.info(f"📈 Applied {strategy.value} correction with confidence {attempt.confidence:.2f}")
                    return attempt.corrected_query
            
            # If no high-confidence corrections, return the best one if in aggressive mode
            if strategy == CorrectionStrategy.AGGRESSIVE and correction_attempts:
                best_attempt = correction_attempts[0]
                logger.info(f"🎯 Applied aggressive correction with confidence {best_attempt.confidence:.2f}")
                return best_attempt.corrected_query
                
        except Exception as e:
            logger.error(f"❌ Error in progressive strategy {strategy.value}: {e}")
        
        return query
    
    def _log_successful_execution(self, original_query: str, executed_query: str, 
                                result: str, attempts: int, execution_time: float):
        """Log successful query execution with recovery details."""
        was_corrected = original_query != executed_query
        
        if was_corrected:
            logger.info(f"✅ Query executed successfully after correction (attempt {attempts + 1})")
            logger.debug(f"Original: {original_query[:100]}...")
            logger.debug(f"Corrected: {executed_query[:100]}...")
            self._enhanced_stats["successful_retries"] += 1
        else:
            logger.debug(f"✅ Query executed successfully on first attempt")
        
        # Log performance metrics
        if execution_time > 5.0:
            logger.info(f"⏱️ Query execution time: {execution_time:.2f}s")
        
        # Update performance improvement stats
        if was_corrected and "LIMIT" in executed_query and "LIMIT" not in original_query:
            self._enhanced_stats["performance_improvements"] += 1
    
    def _handle_final_error(self, original_query: str, final_query: str, 
                           error_message: str, attempts: int, execution_time: float) -> str:
        """Handle the final error when all recovery attempts have failed."""
        # Get suggestions for manual correction
        suggestions = self._correction_service.get_correction_suggestions(final_query)
        
        # Create detailed error response
        error_response = f"❌ Query execution failed after {attempts + 1} attempts.\n"
        error_response += f"⏱️ Total time: {execution_time:.2f}s\n"
        error_response += f"🔍 Final error: {error_message}\n"
        
        if original_query != final_query:
            error_response += f"🔧 Query was modified during retry attempts.\n"
        
        if suggestions:
            error_response += f"\n💡 Suggestions for manual correction:\n"
            for i, suggestion in enumerate(suggestions[:3], 1):  # Limit to top 3 suggestions
                error_response += f"  {i}. {suggestion['description']} (confidence: {suggestion['confidence']:.1%})\n"
        
        # Update final statistics
        self._enhanced_stats["last_error_recovery"] = {
            "timestamp": datetime.now().isoformat(),
            "original_query": original_query[:100] + "..." if len(original_query) > 100 else original_query,
            "final_query": final_query[:100] + "..." if len(final_query) > 100 else final_query,
            "error_message": error_message,
            "attempts": attempts + 1,
            "execution_time": execution_time,
            "suggestions_count": len(suggestions)
        }
        
        logger.error(f"❌ Final error after {attempts + 1} attempts: {error_message}")
        return error_response
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics including security and error recovery."""
        security_stats = self.get_security_stats()
        recovery_stats = self._error_recovery_engine.get_recovery_stats()
        correction_stats = self._correction_service.get_correction_stats()
        
        total_queries = self._security_stats["total_queries"]
        queries_with_errors = self._enhanced_stats["queries_with_errors"]
        auto_corrected = self._enhanced_stats["queries_auto_corrected"]
        
        return {
            "overview": {
                "total_queries_processed": total_queries,
                "queries_with_errors": queries_with_errors,
                "error_rate": (queries_with_errors / max(total_queries, 1)) * 100,
                "auto_correction_rate": (auto_corrected / max(queries_with_errors, 1)) * 100,
                "overall_success_rate": ((total_queries - queries_with_errors + auto_corrected) / max(total_queries, 1)) * 100
            },
            "security_stats": security_stats,
            "error_recovery_stats": recovery_stats,
            "correction_stats": correction_stats,
            "enhanced_features": self._enhanced_stats,
            "performance_metrics": {
                "queries_optimized": self._enhanced_stats["performance_improvements"],
                "retry_success_rate": (self._enhanced_stats["successful_retries"] / max(self._enhanced_stats["retry_attempts"], 1)) * 100,
                "most_used_strategies": dict(sorted(
                    self._enhanced_stats["correction_strategies_used"].items(),
                    key=lambda x: x[1], reverse=True
                ))
            }
        }
    
    def reset_enhanced_stats(self):
        """Reset all statistics (security, recovery, and enhanced features)."""
        super().reset_security_stats()
        self._error_recovery_engine.reset_stats()
        self._correction_service.reset_stats()
        
        self._enhanced_stats = {
            "queries_with_errors": 0,
            "queries_auto_corrected": 0,
            "retry_attempts": 0,
            "successful_retries": 0,
            "correction_strategies_used": {s.value: 0 for s in CorrectionStrategy},
            "error_types_encountered": {},
            "performance_improvements": 0,
            "last_error_recovery": None
        }
        
        logger.info("📊 Enhanced SQL tool statistics reset")
    
    def configure_error_recovery(self, max_retries: int = 3, auto_correction: bool = True,
                               progressive_strategies: bool = True, confidence_threshold: float = 0.6):
        """Configure error recovery behavior."""
        self._max_retry_attempts = max_retries
        self._enable_auto_correction = auto_correction
        self._enable_progressive_strategies = progressive_strategies
        self._correction_confidence_threshold = confidence_threshold
        
        logger.info(f"🔧 Error recovery configured: retries={max_retries}, auto_correction={auto_correction}, "
                   f"progressive={progressive_strategies}, threshold={confidence_threshold}")
    
    def get_query_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Get optimization and correction suggestions for a query without executing it."""
        try:
            # Get suggestions from correction service
            suggestions = self._correction_service.get_correction_suggestions(query)
            
            # Add security-related suggestions
            is_safe, _, security_details = self._validate_query_security(query)
            
            if not is_safe:
                for violation in security_details.get("violations", []):
                    suggestions.append({
                        "type": "security_violation",
                        "description": f"Security issue: {violation}",
                        "confidence": 1.0,
                        "severity": "critical"
                    })
            
            for warning in security_details.get("warnings", []):
                suggestions.append({
                    "type": "security_warning",
                    "description": f"Security warning: {warning}",
                    "confidence": 0.8,
                    "severity": "medium"
                })
            
            # Sort by severity and confidence
            severity_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
            suggestions.sort(key=lambda x: (severity_order.get(x["severity"], 0), x["confidence"]), reverse=True)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Error getting query suggestions: {e}")
            return []
    
    async def _arun(self, query: str, run_manager: Optional[Any] = None) -> str:
        """Execute the query asynchronously with enhanced features."""
        return self._run(query, run_manager)



