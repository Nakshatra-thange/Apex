import os
from dotenv import load_dotenv
from arq import create_pool
from arq.connections import RedisSettings

# Load environment variables to get Redis connection details
load_dotenv()

# This object will hold our connection pool
redis_pool = None

async def get_redis_pool():
    """
    Returns the existing Redis connection pool.
    This function will be used as a dependency in our API endpoints.
    """
    return redis_pool

async def startup_redis_pool():
    """
    This function is called when the FastAPI app starts.
    It creates the Redis connection pool.
    """
    global redis_pool
    
    # --- THIS SECTION IS NOW CORRECTED ---
    # We create the RedisSettings object the correct way, using individual
    # arguments read from our environment variables.
    redis_settings = RedisSettings(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        database=0 # The job queue is on database 0
    )
    # --- END OF CORRECTION ---
    
    redis_pool = await create_pool(redis_settings)

async def shutdown_redis_pool():
    """
    This function is called when the FastAPI app shuts down.
    It gracefully closes the Redis connection pool.
    """
    if redis_pool:
        await redis_pool.close()
