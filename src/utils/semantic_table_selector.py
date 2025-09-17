#!/usr/bin/env python3
"""
Semantic Table Selector for Universal SQL Agent

This module implements intelligent table selection using semantic similarity matching
to optimize token usage and improve query performance by sending only the most
relevant database tables to the LLM.

Based on research from RSL-SQL and other state-of-the-art Text-to-SQL systems.
"""

import os
import logging
import json
import pickle
import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class IndexingStatus(Enum):
    """Status of the semantic table indexing process."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class IndexingProgress:
    """Tracks progress of semantic table indexing."""

    def __init__(self):
        self.status = IndexingStatus.NOT_STARTED
        self.total_tables = 0
        self.processed_tables = 0
        self.successful_tables = 0
        self.failed_tables = 0
        self.start_time = None
        self.end_time = None
        self.current_table = None
        self.error_message = None
        self.failed_table_names = []
        self._lock = threading.Lock()

    def start(self, total_tables: int):
        """Start the indexing process."""
        with self._lock:
            self.status = IndexingStatus.IN_PROGRESS
            self.total_tables = total_tables
            self.processed_tables = 0
            self.successful_tables = 0
            self.failed_tables = 0
            self.start_time = datetime.now()
            self.end_time = None
            self.current_table = None
            self.error_message = None
            self.failed_table_names = []

    def update(self, table_name: str, success: bool, error: str = None):
        """Update progress for a processed table."""
        with self._lock:
            self.processed_tables += 1
            self.current_table = table_name
            if success:
                self.successful_tables += 1
            else:
                self.failed_tables += 1
                if error:
                    self.failed_table_names.append(f"{table_name}: {error}")

    def complete(self, success: bool = True, error_message: str = None):
        """Mark the indexing as completed."""
        with self._lock:
            self.status = IndexingStatus.COMPLETED if success else IndexingStatus.FAILED
            self.end_time = datetime.now()
            self.current_table = None
            if error_message:
                self.error_message = error_message

    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        with self._lock:
            elapsed_time = None
            estimated_remaining = None

            if self.start_time:
                elapsed_time = (datetime.now() - self.start_time).total_seconds()

                if self.processed_tables > 0 and self.status == IndexingStatus.IN_PROGRESS:
                    avg_time_per_table = elapsed_time / self.processed_tables
                    remaining_tables = self.total_tables - self.processed_tables
                    estimated_remaining = avg_time_per_table * remaining_tables

            return {
                "status": self.status.value,
                "total_tables": self.total_tables,
                "processed_tables": self.processed_tables,
                "successful_tables": self.successful_tables,
                "failed_tables": self.failed_tables,
                "current_table": self.current_table,
                "progress_percentage": (self.processed_tables / self.total_tables * 100) if self.total_tables > 0 else 0,
                "elapsed_time_seconds": elapsed_time,
                "estimated_remaining_seconds": estimated_remaining,
                "error_message": self.error_message,
                "failed_table_count": len(self.failed_table_names),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None
            }


class SemanticTableSelector:
    """
    Semantic table selector that uses embedding-based similarity matching
    to identify the most relevant database tables for a given question.
    
    Features:
    - Bidirectional schema linking (forward and backward)
    - Configurable similarity thresholds
    - Embedding caching for performance
    - Graceful fallback mechanisms
    - Token usage optimization tracking
    """
    
    def __init__(self,
                 model_name: str = "all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.3,
                 max_tables: int = 8,
                 cache_dir: str = "vector_store_data/table_embeddings",
                 enabled: bool = True,
                 progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the semantic table selector.

        Args:
            model_name: Name of the sentence transformer model to use
            similarity_threshold: Minimum similarity score for table inclusion
            max_tables: Maximum number of tables to select
            cache_dir: Directory for caching embeddings
            enabled: Whether semantic selection is enabled
            progress_callback: Optional callback function for progress updates
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.max_tables = max_tables
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.progress_callback = progress_callback

        # Lazy loading attributes
        self._model = None
        self._table_embeddings = {}
        self._embedding_cache = {}
        self._cache_timestamp = None

        # Progress tracking
        self.indexing_progress = IndexingProgress()
        self._indexing_thread = None
        self._indexing_lock = threading.Lock()

        # Performance tracking
        self.selection_stats = {
            "total_selections": 0,
            "tables_filtered": 0,
            "cache_hits": 0,
            "fallback_used": 0,
            "avg_similarity_score": 0.0
        }

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Load cached embeddings if available
        if enabled:
            cache_loaded = self._load_embeddings_cache()
            if cache_loaded:
                self.indexing_progress.status = IndexingStatus.COMPLETED
                logger.info(f"✅ Loaded {len(self._table_embeddings)} cached table embeddings")
            else:
                logger.info("No valid cached embeddings found, will build new index")
        else:
            logger.info("Semantic table selection is disabled")

        logger.info(f"SemanticTableSelector initialized: enabled={enabled}, "
                   f"model={model_name}, threshold={similarity_threshold}")
    
    @property
    def model(self) -> Optional[SentenceTransformer]:
        """Lazy load the sentence transformer model."""
        if not self.enabled:
            return None
            
        if self._model is None:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer model: {e}")
                logger.warning("Semantic table selection will be disabled")
                self.enabled = False
                return None
        return self._model
    
    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for text embeddings."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text with caching."""
        if not self.model:
            return None
            
        cache_key = self._get_cache_key(text)
        
        # Check memory cache
        if cache_key in self._embedding_cache:
            self.selection_stats["cache_hits"] += 1
            return self._embedding_cache[cache_key]
        
        try:
            # Generate embedding
            embedding = self.model.encode([text])[0]
            
            # Cache in memory
            self._embedding_cache[cache_key] = embedding
            
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            return None
    
    def build_table_embeddings(self, table_info: Dict[str, Any]) -> None:
        """
        Build and cache embeddings for database tables synchronously.

        Args:
            table_info: Dictionary containing table information
        """
        if not self.enabled:
            logger.warning("Semantic table selection disabled, skipping embedding generation")
            self.indexing_progress.status = IndexingStatus.DISABLED
            return

        if not self.model:
            logger.error("Model not available, cannot build embeddings")
            self.indexing_progress.complete(success=False, error_message="Model not available")
            return

        # If this is an incremental update, adjust the progress tracking
        total_existing = len(self._table_embeddings)
        total_to_process = len(table_info)

        if total_existing > 0:
            logger.info(f"Building embeddings for {total_to_process} new tables (keeping {total_existing} cached)")
        else:
            logger.info(f"Building embeddings for {total_to_process} tables")

        self.indexing_progress.start(total_to_process)

        successful_count = 0

        for table_name, info in table_info.items():
            try:
                # Create comprehensive text representation of the table
                table_text_parts = [table_name]

                # Add column names
                if "columns" in info and info["columns"]:
                    table_text_parts.extend(info["columns"])

                # Add table description if available
                if "description" in info and info["description"]:
                    table_text_parts.append(info["description"])

                # Create searchable text
                table_text = " ".join(table_text_parts).lower()

                # Generate embedding
                embedding = self._get_embedding(table_text)
                if embedding is not None:
                    self._table_embeddings[table_name] = {
                        "embedding": embedding,
                        "text": table_text,
                        "columns": info.get("columns", []),
                        "timestamp": datetime.now()
                    }
                    successful_count += 1
                    self.indexing_progress.update(table_name, success=True)
                else:
                    self.indexing_progress.update(table_name, success=False, error="Failed to generate embedding")

            except Exception as e:
                error_msg = f"Failed to build embedding: {str(e)}"
                logger.error(f"Table {table_name}: {error_msg}")
                self.indexing_progress.update(table_name, success=False, error=error_msg)

        self.indexing_progress.complete(success=True)
        logger.info(f"Successfully built embeddings for {successful_count}/{len(table_info)} tables")

        # Save to disk cache
        self._save_embeddings_cache()

    def build_table_embeddings_async(self, table_info: Dict[str, Any]) -> None:
        """
        Build table embeddings asynchronously in a background thread.

        Args:
            table_info: Dictionary containing table information
        """
        # Check if indexing is already in progress
        if self._indexing_thread and self._indexing_thread.is_alive():
            logger.warning("Table indexing already in progress, skipping new request")
            return

        # Check if we already have valid cached embeddings
        if self._is_indexing_complete_and_valid(table_info):
            logger.info(f"✅ Using cached embeddings for {len(self._table_embeddings)} tables (no changes needed)")
            return
        else:
            logger.info(f"🔄 Cache validation failed, will proceed with indexing")

        # Check if we need to index only new tables
        if len(self._table_embeddings) > 0 and self.indexing_progress.status == IndexingStatus.COMPLETED:
            cached_tables = set(self._table_embeddings.keys())
            new_tables = set(table_info.keys())
            missing_tables = new_tables - cached_tables
            
            if missing_tables:
                logger.info(f"🔄 Found {len(missing_tables)} new tables to index (keeping {len(cached_tables)} cached)")
                # Filter table_info to only include missing tables
                table_info = {name: info for name, info in table_info.items() if name in missing_tables}
            else:
                logger.info(f"✅ All tables already indexed, using cached embeddings")
                return

        def indexing_worker():
            """Worker function for background indexing."""
            try:
                logger.info(f"🧠 Starting background semantic table indexing for {len(table_info)} tables...")
                self.build_table_embeddings(table_info)

                # Call progress callback if provided
                if self.progress_callback:
                    self.progress_callback(self.get_indexing_status())

                logger.info("✅ Semantic table indexing completed successfully")

            except Exception as e:
                error_msg = f"Background indexing failed: {str(e)}"
                logger.error(error_msg)
                self.indexing_progress.complete(success=False, error_message=error_msg)

                if self.progress_callback:
                    self.progress_callback(self.get_indexing_status())

        # Start background thread
        self._indexing_thread = threading.Thread(target=indexing_worker, daemon=True)
        self._indexing_thread.start()

        logger.info("🚀 Semantic table indexing started in background thread")

    def _is_indexing_complete_and_valid(self, table_info: Dict[str, Any]) -> bool:
        """Check if indexing is complete and valid for the given tables."""
        logger.debug(f"Checking cache validity: embeddings={len(self._table_embeddings)}, status={self.indexing_progress.status}")
        
        if not self._table_embeddings:
            logger.debug("No table embeddings in memory")
            return False
            
        if self.indexing_progress.status != IndexingStatus.COMPLETED:
            logger.debug(f"Indexing not completed, status: {self.indexing_progress.status}")
            return False
        
        # Check if all required tables are cached
        cached_tables = set(self._table_embeddings.keys())
        required_tables = set(table_info.keys())
        
        logger.debug(f"Cached tables: {len(cached_tables)}, Required tables: {len(required_tables)}")
        
        if not required_tables.issubset(cached_tables):
            missing = required_tables - cached_tables
            logger.debug(f"Missing tables: {missing}")
            return False
        
        # Check cache age (24 hours)
        try:
            cache_file = os.path.join(self.cache_dir, "table_embeddings.pkl")
            if os.path.exists(cache_file):
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                is_recent = cache_age < timedelta(days=7)
                logger.debug(f"Cache age: {cache_age}, is recent: {is_recent}")
                return is_recent
            else:
                logger.debug("Cache file does not exist")
                return False
        except Exception as e:
            logger.warning(f"Error checking cache age: {e}")
            return False

    def get_indexing_status(self) -> Dict[str, Any]:
        """Get current indexing status and progress."""
        progress_info = self.indexing_progress.get_progress_info()

        # Add additional status information
        progress_info.update({
            "is_indexing_active": self._indexing_thread and self._indexing_thread.is_alive(),
            "embeddings_available": len(self._table_embeddings) > 0,
            "cached_embeddings_count": len(self._table_embeddings),
            "model_loaded": self._model is not None,
            "enabled": self.enabled
        })

        return progress_info

    def wait_for_indexing_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for indexing to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if indexing completed, False if timeout occurred
        """
        if not self._indexing_thread:
            return True

        try:
            self._indexing_thread.join(timeout=timeout)
            return not self._indexing_thread.is_alive()
        except Exception as e:
            logger.error(f"Error waiting for indexing completion: {e}")
            return False
    
    def _save_embeddings_cache(self) -> None:
        """Save embeddings to disk cache."""
        try:
            cache_file = os.path.join(self.cache_dir, "table_embeddings.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(self._table_embeddings, f)
            logger.debug(f"Saved table embeddings cache to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save embeddings cache: {e}")
    
    def _load_embeddings_cache(self) -> bool:
        """Load embeddings from disk cache."""
        try:
            cache_file = os.path.join(self.cache_dir, "table_embeddings.pkl")
            if os.path.exists(cache_file):
                # Check cache age
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                
                # Load cache if it's less than 7 days old (more lenient)
                max_cache_age = timedelta(days=7)
                if cache_age < max_cache_age:
                    with open(cache_file, 'rb') as f:
                        self._table_embeddings = pickle.load(f)
                    logger.info(f"Loaded {len(self._table_embeddings)} table embeddings from cache (age: {cache_age})")
                    return True
                else:
                    logger.info(f"Embeddings cache is too old ({cache_age}), will rebuild")
            return False
        except Exception as e:
            logger.warning(f"Failed to load embeddings cache: {e}")
            return False

    def is_cache_valid_for_tables(self, table_names: List[str]) -> bool:
        """
        Check if the current cache is valid for the given table names.

        Args:
            table_names: List of table names to check

        Returns:
            True if cache covers all tables and is recent, False otherwise
        """
        if not self._table_embeddings:
            logger.debug("No table embeddings in memory")
            return False

        # Check if all tables are cached
        cached_tables = set(self._table_embeddings.keys())
        required_tables = set(table_names)

        if not required_tables.issubset(cached_tables):
            missing_tables = required_tables - cached_tables
            logger.debug(f"Missing tables in cache: {missing_tables}")
            return False

        # Check cache age (24 hours)
        try:
            cache_file = os.path.join(self.cache_dir, "table_embeddings.pkl")
            if os.path.exists(cache_file):
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                is_recent = cache_age < timedelta(days=7)
                logger.debug(f"Cache age: {cache_age}, is recent: {is_recent}")
                return is_recent
            else:
                logger.debug("Cache file does not exist")
                return False
        except Exception as e:
            logger.warning(f"Error checking cache age: {e}")
            return False

    def get_table_relevance_scores(self, question: str) -> Dict[str, float]:
        """
        Calculate relevance scores for all tables based on the question.
        
        Args:
            question: User's natural language question
            
        Returns:
            Dictionary mapping table names to relevance scores (0.0 to 1.0)
        """
        if not self.enabled or not self.model or not self._table_embeddings:
            return {}
        
        try:
            # Get question embedding
            question_embedding = self._get_embedding(question.lower())
            if question_embedding is None:
                return {}
            
            scores = {}
            table_embeddings = []
            table_names = []
            
            # Collect all table embeddings
            for table_name, table_data in self._table_embeddings.items():
                table_embeddings.append(table_data["embedding"])
                table_names.append(table_name)
            
            if not table_embeddings:
                return {}
            
            # Calculate cosine similarities
            similarities = cosine_similarity(
                [question_embedding], 
                table_embeddings
            )[0]
            
            # Create scores dictionary
            for i, table_name in enumerate(table_names):
                scores[table_name] = float(similarities[i])
            
            # Update statistics
            if scores:
                self.selection_stats["avg_similarity_score"] = np.mean(list(scores.values()))
            
            return scores
            
        except Exception as e:
            logger.error(f"Failed to calculate table relevance scores: {e}")
            return {}
    
    def select_relevant_tables(self,
                             question: str,
                             available_tables: List[str],
                             max_tables: Optional[int] = None) -> List[str]:
        """
        Select the most relevant tables for a given question using semantic similarity.

        Args:
            question: User's natural language question
            available_tables: List of all available table names
            max_tables: Maximum number of tables to select (overrides default)

        Returns:
            List of selected table names, ordered by relevance
        """
        self.selection_stats["total_selections"] += 1
        max_tables = max_tables or self.max_tables

        # Fallback: if semantic selection is disabled
        if not self.enabled:
            logger.debug("Semantic selection disabled, using fallback")
            self.selection_stats["fallback_used"] += 1
            return available_tables[:max_tables]

        # Check if indexing is in progress
        if self.indexing_progress.status == IndexingStatus.IN_PROGRESS:
            progress = self.indexing_progress.get_progress_info()
            logger.info(f"🔄 Semantic indexing in progress ({progress['progress_percentage']:.1f}% complete), using fallback selection")
            self.selection_stats["fallback_used"] += 1
            return available_tables[:max_tables]

        # Check if indexing failed
        if self.indexing_progress.status == IndexingStatus.FAILED:
            logger.warning(f"❌ Semantic indexing failed: {self.indexing_progress.error_message}, using fallback")
            self.selection_stats["fallback_used"] += 1
            return available_tables[:max_tables]

        # Ensure we have embeddings for available tables
        if not self._table_embeddings:
            logger.warning("No table embeddings available, using fallback")
            self.selection_stats["fallback_used"] += 1
            return available_tables[:max_tables]
        
        try:
            # Get relevance scores
            scores = self.get_table_relevance_scores(question)
            if not scores:
                logger.warning("Failed to get relevance scores, using fallback")
                self.selection_stats["fallback_used"] += 1
                return available_tables[:max_tables]
            
            # Filter tables that are actually available
            available_scores = {
                table: score for table, score in scores.items() 
                if table in available_tables
            }
            
            # Sort by relevance score (descending)
            sorted_tables = sorted(
                available_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Apply similarity threshold and max_tables limit
            selected_tables = []
            for table_name, score in sorted_tables:
                if score >= self.similarity_threshold and len(selected_tables) < max_tables:
                    selected_tables.append(table_name)
            
            # Fallback: if too few tables selected, add more based on original order
            if len(selected_tables) < 3:
                logger.info(f"Only {len(selected_tables)} tables met similarity threshold, "
                           f"adding more for robustness")
                remaining_tables = [t for t in available_tables if t not in selected_tables]
                selected_tables.extend(remaining_tables[:max_tables - len(selected_tables)])
            
            # Track statistics
            self.selection_stats["tables_filtered"] += len(available_tables) - len(selected_tables)
            
            logger.info(f"Selected {len(selected_tables)} tables from {len(available_tables)} "
                       f"available (threshold: {self.similarity_threshold})")
            
            if logger.isEnabledFor(logging.DEBUG):
                for table in selected_tables[:5]:  # Log top 5
                    score = available_scores.get(table, 0.0)
                    logger.debug(f"  {table}: {score:.3f}")
            
            return selected_tables
            
        except Exception as e:
            logger.error(f"Error in semantic table selection: {e}")
            self.selection_stats["fallback_used"] += 1
            return available_tables[:max_tables]
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the table selector."""
        # Calculate token savings estimate
        token_savings_pct = 0.0
        if self.selection_stats["total_selections"] > 0:
            avg_tables_filtered = self.selection_stats["tables_filtered"] / self.selection_stats["total_selections"]
            # Rough estimate: each table schema averages ~200 tokens
            token_savings_pct = (avg_tables_filtered * 200) / (self.max_tables * 200) * 100

        # Include indexing status
        indexing_status = self.get_indexing_status()

        return {
            **self.selection_stats,
            "enabled": self.enabled,
            "model_name": self.model_name,
            "similarity_threshold": self.similarity_threshold,
            "max_tables": self.max_tables,
            "cached_tables": len(self._table_embeddings),
            "cache_size": len(self._embedding_cache),
            "estimated_token_savings_pct": round(token_savings_pct, 2),
            "indexing_status": indexing_status
        }
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._table_embeddings.clear()
        self._embedding_cache.clear()
        logger.info("Cleared semantic table selector caches")

    def enable_semantic_selection(self) -> None:
        """Enable semantic table selection."""
        self.enabled = True
        logger.info("Semantic table selection enabled")

    def disable_semantic_selection(self) -> None:
        """Disable semantic table selection."""
        self.enabled = False
        logger.info("Semantic table selection disabled")

    def force_rebuild_index(self) -> None:
        """Force rebuild of the semantic index by clearing cache and resetting status."""
        self.clear_cache()
        self.indexing_progress.status = IndexingStatus.NOT_STARTED
        logger.info("Semantic index marked for rebuild")

    def get_user_control_options(self) -> Dict[str, Any]:
        """Get user control options and current status."""
        return {
            "enabled": self.enabled,
            "indexing_status": self.indexing_progress.status.value,
            "cached_tables": len(self._table_embeddings),
            "can_rebuild": True,
            "can_enable": True,
            "can_disable": True,
            "is_indexing_active": self._indexing_thread and self._indexing_thread.is_alive()
        }

    def validate_cache_for_tables(self, table_names: List[str]) -> Dict[str, Any]:
        """Validate cache for specific tables and return detailed information."""
        result = {
            "cache_exists": len(self._table_embeddings) > 0,
            "indexing_complete": self.indexing_progress.status == IndexingStatus.COMPLETED,
            "cached_tables": len(self._table_embeddings),
            "required_tables": len(table_names),
            "missing_tables": [],
            "cache_age_valid": False,
            "overall_valid": False
        }
        
        if not result["cache_exists"]:
            return result
            
        if not result["indexing_complete"]:
            return result
            
        # Check missing tables
        cached_tables = set(self._table_embeddings.keys())
        required_tables = set(table_names)
        missing = required_tables - cached_tables
        result["missing_tables"] = list(missing)
        
        # Check cache age
        try:
            cache_file = os.path.join(self.cache_dir, "table_embeddings.pkl")
            if os.path.exists(cache_file):
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                result["cache_age_valid"] = cache_age < timedelta(days=7)
                result["cache_age_hours"] = cache_age.total_seconds() / 3600
        except Exception as e:
            result["cache_age_error"] = str(e)
        
        # Overall validity
        result["overall_valid"] = (
            result["cache_exists"] and 
            result["indexing_complete"] and 
            len(result["missing_tables"]) == 0 and 
            result["cache_age_valid"]
        )
        
        return result


def create_semantic_table_selector(force_enabled: bool = None) -> SemanticTableSelector:
    """
    Factory function to create a SemanticTableSelector with configuration from environment.
    
    Args:
        force_enabled: Override the enabled setting. If None, uses environment variable.
    """
    # Load configuration from environment variables
    if force_enabled is not None:
        enabled = force_enabled
    else:
        enabled = os.getenv("SEMANTIC_TABLE_SELECTION_ENABLED", "true").lower() == "true"
    
    model_name = os.getenv("VS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
    max_tables = int(os.getenv("MAX_RELEVANT_TABLES", "8"))
    cache_dir = os.getenv("VS_CACHE_DIR", "vector_store_data/table_embeddings")
    
    return SemanticTableSelector(
        model_name=model_name,
        similarity_threshold=similarity_threshold,
        max_tables=max_tables,
        cache_dir=cache_dir,
        enabled=enabled
    )





