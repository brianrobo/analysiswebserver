"""
Tests for Redis caching layer
"""
import pytest
from api.core.cache import RedisCache


@pytest.fixture
async def redis_cache():
    """Create and connect Redis cache for testing"""
    cache = RedisCache()
    await cache.connect()

    # Clear all cache before tests
    await cache.clear_all_cache()

    yield cache

    # Cleanup after tests
    await cache.clear_all_cache()
    await cache.disconnect()


@pytest.mark.asyncio
async def test_cache_set_get(redis_cache):
    """Test basic cache set and get"""
    # Set analysis result
    job_id = 123
    result_data = {
        "job_id": job_id,
        "job_name": "Test Analysis",
        "result_data": {"total_files": 10},
        "summary": {"ui_files_count": 5},
        "processing_time": 12.5,
        "created_at": "2026-02-08T10:00:00"
    }

    success = await redis_cache.set_analysis_result(job_id, result_data)
    assert success is True

    # Get cached result
    cached = await redis_cache.get_analysis_result(job_id)
    assert cached is not None
    assert cached["job_id"] == job_id
    assert cached["job_name"] == "Test Analysis"
    assert cached["result_data"]["total_files"] == 10


@pytest.mark.asyncio
async def test_cache_miss(redis_cache):
    """Test cache miss returns None"""
    result = await redis_cache.get_analysis_result(999999)
    assert result is None


@pytest.mark.asyncio
async def test_cache_invalidation(redis_cache):
    """Test cache invalidation"""
    job_id = 456
    result_data = {"job_id": job_id, "data": "test"}

    # Set and verify
    await redis_cache.set_analysis_result(job_id, result_data)
    cached = await redis_cache.get_analysis_result(job_id)
    assert cached is not None

    # Invalidate
    success = await redis_cache.invalidate_analysis_result(job_id)
    assert success is True

    # Verify cache is cleared
    cached_after = await redis_cache.get_analysis_result(job_id)
    assert cached_after is None


@pytest.mark.asyncio
async def test_progress_tracking(redis_cache):
    """Test progress caching"""
    job_id = 789

    # Set progress
    await redis_cache.set_progress(job_id, 50, "running", "Processing files...")

    # Get progress
    progress = await redis_cache.get_progress(job_id)
    assert progress is not None
    assert progress["progress"] == 50
    assert progress["status"] == "running"
    assert progress["message"] == "Processing files..."


@pytest.mark.asyncio
async def test_user_history_caching(redis_cache):
    """Test user history caching"""
    user_id = 100
    history = [
        {"id": 1, "job_name": "Analysis 1", "status": "completed"},
        {"id": 2, "job_name": "Analysis 2", "status": "running"},
    ]

    # Set history
    await redis_cache.set_user_history(user_id, history)

    # Get history
    cached_history = await redis_cache.get_user_history(user_id)
    assert cached_history is not None
    assert len(cached_history) == 2
    assert cached_history[0]["job_name"] == "Analysis 1"
    assert cached_history[1]["status"] == "running"


@pytest.mark.asyncio
async def test_cache_stats(redis_cache):
    """Test cache statistics tracking"""
    # Generate some cache hits and misses
    await redis_cache.set_analysis_result(1, {"data": "test1"})
    await redis_cache.set_analysis_result(2, {"data": "test2"})

    # Hit
    await redis_cache.get_analysis_result(1)
    await redis_cache.get_analysis_result(2)

    # Miss
    await redis_cache.get_analysis_result(999)
    await redis_cache.get_analysis_result(1000)

    # Get stats
    stats = await redis_cache.get_cache_stats()
    assert stats["cache_hits"] >= 2
    assert stats["cache_misses"] >= 2
    assert stats["total_requests"] >= 4
    assert 0 <= stats["hit_rate_percentage"] <= 100


@pytest.mark.asyncio
async def test_clear_all_cache(redis_cache):
    """Test clearing all cache"""
    # Set multiple cache entries
    await redis_cache.set_analysis_result(1, {"data": "test1"})
    await redis_cache.set_analysis_result(2, {"data": "test2"})
    await redis_cache.set_user_history(100, [{"id": 1}])

    # Clear all
    success = await redis_cache.clear_all_cache()
    assert success is True

    # Verify all cleared
    assert await redis_cache.get_analysis_result(1) is None
    assert await redis_cache.get_analysis_result(2) is None
    assert await redis_cache.get_user_history(100) is None


@pytest.mark.asyncio
async def test_ttl_values(redis_cache):
    """Test that TTL constants are set correctly"""
    assert redis_cache.TTL_RESULT == 86400  # 24 hours
    assert redis_cache.TTL_PROGRESS == 60  # 1 minute
    assert redis_cache.TTL_HISTORY == 300  # 5 minutes
