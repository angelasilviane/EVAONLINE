"""
Integration tests for Redis caching operations.
Tests Redis connectivity, caching, and data operations.
"""


class TestRedisConnection:
    """Test Redis connectivity and basic operations."""

    def test_redis_client_available(self, redis_client):
        """Test that Redis client is available."""
        assert redis_client is not None

    def test_redis_ping(self, redis_client):
        """Test Redis PING command."""
        response = redis_client.ping()
        assert response is True

    def test_redis_set_get(self, redis_client):
        """Test Redis SET and GET operations."""
        key = "test_key"
        value = "test_value"

        redis_client.set(key, value)
        result = redis_client.get(key)

        assert result == value

    def test_redis_set_with_ttl(self, redis_client):
        """Test Redis SET with expiration."""
        key = "test_ttl_key"
        value = "test_value"

        redis_client.set(key, value, ex=10)
        result = redis_client.get(key)

        assert result == value

        # Check TTL
        ttl = redis_client.ttl(key)
        assert ttl > 0
        assert ttl <= 10

    def test_redis_delete(self, redis_client):
        """Test Redis DELETE operation."""
        key = "test_delete_key"
        redis_client.set(key, "value")

        assert redis_client.exists(key) == 1
        redis_client.delete(key)
        assert redis_client.exists(key) == 0

    def test_redis_incr(self, redis_client):
        """Test Redis INCR for counters."""
        key = "counter"
        redis_client.delete(key)

        assert redis_client.incr(key) == 1
        assert redis_client.incr(key) == 2
        assert redis_client.get(key) == "2"

    def test_redis_list_operations(self, redis_client):
        """Test Redis LIST operations."""
        key = "test_list"
        redis_client.delete(key)

        # Push items
        redis_client.rpush(key, "item1", "item2", "item3")
        assert redis_client.llen(key) == 3

        # Pop items
        item = redis_client.lpop(key)
        assert item == "item1"

    def test_redis_hash_operations(self, redis_client):
        """Test Redis HASH operations."""
        key = "test_hash"
        redis_client.delete(key)

        # Set hash fields
        redis_client.hset(
            key, mapping={"field1": "value1", "field2": "value2"}
        )

        # Get hash field
        assert redis_client.hget(key, "field1") == "value1"

        # Get all fields
        data = redis_client.hgetall(key)
        assert data == {"field1": "value1", "field2": "value2"}


class TestRedisCaching:
    """Test caching patterns with Redis."""

    def test_cache_hit_miss(self, redis_client):
        """Test cache hit and miss scenarios."""
        cache_key = "user:1:profile"
        redis_client.delete(cache_key)

        # Miss
        assert redis_client.get(cache_key) is None

        # Set
        redis_client.set(cache_key, "user_data", ex=3600)

        # Hit
        assert redis_client.get(cache_key) == "user_data"

    def test_cache_invalidation(self, redis_client):
        """Test cache invalidation pattern."""
        cache_key = "location:1:climate"
        redis_client.set(cache_key, "old_data", ex=3600)

        # Verify it's there
        assert redis_client.get(cache_key) == "old_data"

        # Invalidate
        redis_client.delete(cache_key)
        assert redis_client.get(cache_key) is None

    def test_session_cache(self, redis_client):
        """Test session caching pattern."""
        session_key = "session:abc123"
        session_data = {"user_id": 1, "username": "testuser"}

        redis_client.hset(session_key, mapping=session_data)
        assert redis_client.hget(session_key, "user_id") == "1"
        assert redis_client.hget(session_key, "username") == "testuser"
