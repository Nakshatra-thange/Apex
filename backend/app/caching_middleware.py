import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import hashlib

from .cache_manager import get_cache, set_cache

# Define which URL paths we want to apply caching to.
CACHEABLE_PATHS = [
    "/projects/",
    "/users/me/stats",
]

class ResponseCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # We only cache safe GET requests
        if request.method != "GET":
            return await call_next(request)

        # Check if the request path is one we want to cache
        if not any(request.url.path.startswith(path) for path in CACHEABLE_PATHS):
            return await call_next(request)

        # Create a unique cache key based on the full URL path and query params
        # This ensures that /projects/1 and /projects/2 have different cache keys
        cache_key = f"api_cache:{hashlib.md5(str(request.url).encode()).hexdigest()}"

        # 1. Check if the response is already in the cache
        cached_response = get_cache(cache_key)
        if cached_response:
            print(f"CACHE HIT for key: {cache_key}")
            # If found, return the cached response immediately
            return Response(
                content=json.dumps(cached_response),
                media_type="application/json",
                headers={"X-Cache-Status": "HIT"}
            )

        print(f"CACHE MISS for key: {cache_key}")
        
        # 2. If not in cache, proceed with the request
        response = await call_next(request)
        
        # 3. Cache the new response if it was successful
        if response.status_code == 200 and isinstance(response, StreamingResponse):
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            try:
                data_to_cache = json.loads(response_body)
                # Cache with a 5-minute TTL
                set_cache(cache_key, data_to_cache, ttl_seconds=300)
            except json.JSONDecodeError:
                pass # Don't cache non-JSON responses
            
            # Re-create the response to send to the client
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
            new_response.headers["X-Cache-Status"] = "MISS"
            return new_response

        response.headers["X-Cache-Status"] = "MISS"
        return response
