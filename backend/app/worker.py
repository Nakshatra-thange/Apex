import os
from dotenv import load_dotenv
from arq.connections import RedisSettings # <-- This import is correct

# Load environment variables
load_dotenv()

from . import tasks

class WorkerSettings:
    """
    Defines the settings for our background job worker.
    """
    queues = ['high_priority', 'default_priority']

    functions = [
        tasks.analyze_code_task,
    ]
    
    # --- THIS SECTION IS NOW CORRECTED ---
    # We create a RedisSettings object by passing individual arguments,
    # NOT from a URL. We read these from our environment variables
    # with sensible defaults.
    redis_settings = RedisSettings(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        database=0 # The job queue is on database 0
    )
    # --- END OF CORRECTION ---

    job_timeout = 300  # 5 minutes
    max_tries = 5
