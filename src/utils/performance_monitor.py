#!/usr/bin/env python3
"""
Performance monitoring module for the Universal SQL Agent.

This module provides comprehensive performance tracking and statistics
for query processing, response times, and optimization metrics.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class PerformanceStats:
    """Data class for performance statistics."""
    total_queries: int = 0
    avg_response_time: float = 0.0
    validation_stats: Dict[str, int] = field(default_factory=lambda: {'compliant_queries': 0})


class PerformanceMonitor:
    """Monitors and tracks performance metrics for the SQL Agent.
    
    This class provides functionality to:
    - Track query statistics and response times
    - Monitor optimization rates and token savings
    - Validate methodology compliance
    - Generate performance summaries
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.query_stats = {
            "total_queries": 0,
            "avg_response_time": 0.0
        }
        self._validation_stats = {'compliant_queries': 0}
        self._start_times = {}  # Track start times for ongoing operations
    
    def start_query_timer(self, query_id: Optional[str] = None) -> str:
        """Start timing a query operation.
        
        Args:
            query_id: Optional identifier for the query. If not provided, generates one.
            
        Returns:
            The query identifier for this timing session.
        """
        if query_id is None:
            query_id = f"query_{int(time.time() * 1000)}"
        
        self._start_times[query_id] = time.time()
        return query_id
    
    def end_query_timer(self, query_id: str) -> float:
        """End timing a query operation and return the elapsed time.
        
        Args:
            query_id: The identifier for the query timing session.
            
        Returns:
            The elapsed time in seconds.
        """
        if query_id not in self._start_times:
            return 0.0
        
        elapsed_time = time.time() - self._start_times[query_id]
        del self._start_times[query_id]
        return elapsed_time
    
    def record_query_completion(self, processing_time: float, 
                              is_validation_compliant: bool = False) -> None:
        """Record the completion of a query with performance metrics.
        
        Args:
            processing_time: Total time taken to process the query in seconds.
            is_validation_compliant: Whether the query followed validation methodology.
        """
        self.query_stats["total_queries"] += 1
        
        if is_validation_compliant:
            self._validation_stats['compliant_queries'] += 1
        
        # Update average response time
        prev_avg = self.query_stats["avg_response_time"]
        total_queries = self.query_stats["total_queries"]
        self.query_stats["avg_response_time"] = (
            (prev_avg * (total_queries - 1)) + processing_time
        ) / total_queries

    def get_validation_compliance_rate(self) -> float:
        """Get the current validation methodology compliance rate as a percentage.
        
        Returns:
            The compliance rate as a percentage (0-100).
        """
        if self.query_stats["total_queries"] == 0:
            return 0.0
        
        return (self._validation_stats['compliant_queries'] / 
                self.query_stats["total_queries"]) * 100
    
    def get_performance_stats(self) -> PerformanceStats:
        """Get current performance statistics as a structured object.
        
        Returns:
            PerformanceStats object containing current metrics.
        """
        return PerformanceStats(
            total_queries=self.query_stats["total_queries"],
            avg_response_time=self.query_stats["avg_response_time"],
            validation_stats=self._validation_stats.copy()
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (placeholder for future cache implementation).
        
        Returns:
            Dictionary containing cache statistics.
        """
        # This is a placeholder for future cache statistics
        # Currently returns basic query stats for compatibility
        return {
            "total_queries": self.query_stats["total_queries"],
            "cache_hits": 0,  # Placeholder
            "cache_misses": 0,  # Placeholder
            "cache_hit_rate": 0.0  # Placeholder
        }
    
    def print_performance_summary(self) -> None:
        """Print a comprehensive performance summary.
        """
        if self.query_stats["total_queries"] == 0:
            print("📊 No queries processed yet.")
            return
        
        print("\n📊 Final Performance Summary:")
        print(f"  Total Queries Processed: {self.query_stats['total_queries']}")
        print(f"  Average Response Time: {self.query_stats['avg_response_time']:.2f}s")
        
        # Add validation methodology compliance tracking
        if self._validation_stats.get('compliant_queries', 0) > 0:
            compliance_rate = self.get_validation_compliance_rate()
            print(f"  Validation Methodology Compliance: {compliance_rate:.1f}%")
    
    def should_show_timing_info(self, processing_time: float, threshold: float = 5.0) -> bool:
        """Determine if timing information should be displayed based on processing time.
        
        Args:
            processing_time: The processing time in seconds.
            threshold: The threshold above which timing info should be shown.
            
        Returns:
            True if timing info should be displayed, False otherwise.
        """
        return processing_time > threshold
    
    def format_timing_message(self, total_time: float, query_time: float) -> str:
        """Format a timing message for display.
        
        Args:
            total_time: Total processing time in seconds.
            query_time: Query execution time in seconds.
            
        Returns:
            Formatted timing message.
        """
        return f"⏱️ Total processing time: {total_time:.2f}s (Query: {query_time:.2f}s)"
    
    def reset_stats(self) -> None:
        """Reset all performance statistics to initial values."""
        self.query_stats = {
            "total_queries": 0,
            "avg_response_time": 0.0
        }
        self._validation_stats = {'compliant_queries': 0}
        self._start_times.clear()
    
    @contextmanager
    def track_operation(self, operation_name: str):
        """Context manager to track the duration of an operation.
        
        Args:
            operation_name: Name of the operation being tracked.
            
        Yields:
            The operation name for reference.
        """
        start_time = time.time()
        try:
            yield operation_name
        finally:
            elapsed_time = time.time() - start_time
            # You can add logging or additional tracking here if needed
            pass





