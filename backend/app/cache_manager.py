# File: apex/backend/app/cache_manager.py
import redis
import json
import os
from dotenv import load_dotenv
from typing import Optional, Dict # <-- ADDED IMPORTS

# Load environment variables
load_dotenv()

# Connect to the Redis Cache Database (db=1)
REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/1")
redis_client = redis.from_url(REDIS_CACHE_URL, decode_responses=True)


def set_cache(key: str, data: Dict, ttl_seconds: int = 3600):
    """
    Stores data in the Redis cache as a JSON string with a TTL.
    """
    try:
        value = json.dumps(data)
        redis_client.set(key, value, ex=ttl_seconds)
    except redis.exceptions.RedisError as e:
        print(f"Error setting cache for key {key}: {e}")
        pass


# --- THIS FUNCTION IS NOW CORRECTED FOR PYTHON 3.9 ---
def get_cache(key: str) -> Optional[Dict]:
    """
    Retrieves and decodes data from the Redis cache.
    Returns None if the key does not exist or an error occurs.
    """
    try:
        cached_value = redis_client.get(key)
        if cached_value:
            return json.loads(cached_value)
        return None
    except redis.exceptions.RedisError as e:
        print(f"Error getting cache for key {key}: {e}")
        return None


def invalidate_cache_by_key(key: str):
    """
    Deletes a specific key from the Redis cache.
    """
    try:
        redis_client.delete(key)
    except redis.exceptions.RedisError as e:
        print(f"Error invalidating cache for key {key}: {e}")


def invalidate_cache_by_pattern(pattern: str):
    """
    Deletes all keys matching a specific pattern.
    """
    try:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
    except redis.exceptions.RedisError as e:
        print(f"Error invalidating cache with pattern {pattern}: {e}")