"""
Redis caching layer for analysis results and user history
Provides high-performance caching with TTL support
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta

import redis.asyncio as aioredis
from redis.asyncio import Redis
from api.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis caching service for analysis results, progress, and user history

    Cache Key Patterns:
    - analysis:result:{job_id}     (TTL: 24h)
    - analysis:progress:{job_id}   (TTL: 1min)
    - user:history:{user_id}       (TTL: 5min)
    - stats:cache_hits             (permanent)
    - stats:cache_misses           (permanent)
    """

    def __init__(self):
        self._redis: Optional[Redis] = None

        # TTL constants
        self.TTL_RESULT = int(timedelta(hours=24).total_seconds())
        self.TTL_PROGRESS = int(timedelta(minutes=1).total_seconds())
        self.TTL_HISTORY = int(timedelta(minutes=5).total_seconds())

    async def connect(self):
        """Initialize Redis connection pool"""
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=10
                )
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None

    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    @property
    def redis(self) -> Redis:
        """Get Redis client, raise if not connected"""
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis

    # ============ Analysis Result Caching ============

    async def set_analysis_result(self, job_id: int, result: Dict[str, Any]) -> bool:
        """
        Cache analysis result

        Args:
            job_id: Analysis job ID
            result: Analysis result dictionary

        Returns:
            True if cached successfully
        """
        try:
            key = f"analysis:result:{job_id}"
            value = json.dumps(result, ensure_ascii=False)
            await self.redis.setex(key, self.TTL_RESULT, value)
            logger.debug(f"Cached analysis result for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache analysis result: {e}")
            return False

    async def get_analysis_result(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis result

        Args:
            job_id: Analysis job ID

        Returns:
            Analysis result dict or None if not found
        """
        try:
            key = f"analysis:result:{job_id}"
            value = await self.redis.get(key)

            if value:
                await self._increment_cache_hits()
                logger.debug(f"Cache HIT for analysis result {job_id}")
                return json.loads(value)
            else:
                await self._increment_cache_misses()
                logger.debug(f"Cache MISS for analysis result {job_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to get cached analysis result: {e}")
            await self._increment_cache_misses()
            return None

    async def invalidate_analysis_result(self, job_id: int) -> bool:
        """
        Invalidate cached analysis result

        Args:
            job_id: Analysis job ID

        Returns:
            True if invalidated successfully
        """
        try:
            key = f"analysis:result:{job_id}"
            await self.redis.delete(key)
            logger.debug(f"Invalidated analysis result cache for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate analysis result: {e}")
            return False

    # ============ Progress Tracking ============

    async def set_progress(self, job_id: int, progress: int, status: str, message: str = "") -> bool:
        """
        Cache analysis progress

        Args:
            job_id: Analysis job ID
            progress: Progress percentage (0-100)
            status: Job status (pending/running/completed/failed)
            message: Optional progress message

        Returns:
            True if cached successfully
        """
        try:
            key = f"analysis:progress:{job_id}"
            value = json.dumps({
                "progress": progress,
                "status": status,
                "message": message
            }, ensure_ascii=False)
            await self.redis.setex(key, self.TTL_PROGRESS, value)
            return True
        except Exception as e:
            logger.error(f"Failed to cache progress: {e}")
            return False

    async def get_progress(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis progress

        Args:
            job_id: Analysis job ID

        Returns:
            Progress dict or None if not found
        """
        try:
            key = f"analysis:progress:{job_id}"
            value = await self.redis.get(key)

            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached progress: {e}")
            return None

    # ============ User History Caching ============

    async def set_user_history(self, user_id: int, history: List[Dict[str, Any]]) -> bool:
        """
        Cache user analysis history (first page only)

        Args:
            user_id: User ID
            history: List of analysis job summaries

        Returns:
            True if cached successfully
        """
        try:
            key = f"user:history:{user_id}"
            value = json.dumps(history, ensure_ascii=False)
            await self.redis.setex(key, self.TTL_HISTORY, value)
            logger.debug(f"Cached user history for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache user history: {e}")
            return False

    async def get_user_history(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached user analysis history

        Args:
            user_id: User ID

        Returns:
            List of analysis job summaries or None if not found
        """
        try:
            key = f"user:history:{user_id}"
            value = await self.redis.get(key)

            if value:
                await self._increment_cache_hits()
                logger.debug(f"Cache HIT for user history {user_id}")
                return json.loads(value)
            else:
                await self._increment_cache_misses()
                logger.debug(f"Cache MISS for user history {user_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to get cached user history: {e}")
            await self._increment_cache_misses()
            return None

    async def invalidate_user_history(self, user_id: int) -> bool:
        """
        Invalidate cached user history

        Args:
            user_id: User ID

        Returns:
            True if invalidated successfully
        """
        try:
            key = f"user:history:{user_id}"
            await self.redis.delete(key)
            logger.debug(f"Invalidated user history cache for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user history: {e}")
            return False

    # ============ Cache Statistics ============

    async def _increment_cache_hits(self):
        """Increment cache hit counter"""
        try:
            await self.redis.incr("stats:cache_hits")
        except Exception as e:
            logger.error(f"Failed to increment cache hits: {e}")

    async def _increment_cache_misses(self):
        """Increment cache miss counter"""
        try:
            await self.redis.incr("stats:cache_misses")
        except Exception as e:
            logger.error(f"Failed to increment cache misses: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache hits, misses, and hit rate
        """
        try:
            hits = await self.redis.get("stats:cache_hits") or "0"
            misses = await self.redis.get("stats:cache_misses") or "0"

            hits_int = int(hits)
            misses_int = int(misses)
            total = hits_int + misses_int

            hit_rate = (hits_int / total * 100) if total > 0 else 0.0

            return {
                "cache_hits": hits_int,
                "cache_misses": misses_int,
                "total_requests": total,
                "hit_rate_percentage": round(hit_rate, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "cache_hits": 0,
                "cache_misses": 0,
                "total_requests": 0,
                "hit_rate_percentage": 0.0
            }

    async def clear_all_cache(self) -> bool:
        """
        Clear all analysis-related cache (for testing/maintenance)

        Returns:
            True if cleared successfully
        """
        try:
            # Get all analysis-related keys
            keys_to_delete = []

            async for key in self.redis.scan_iter(match="analysis:*"):
                keys_to_delete.append(key)

            async for key in self.redis.scan_iter(match="user:history:*"):
                keys_to_delete.append(key)

            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
                logger.info(f"Cleared {len(keys_to_delete)} cache entries")

            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Global cache instance
cache = RedisCache()
