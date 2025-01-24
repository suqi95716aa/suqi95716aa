import asyncio
from functools import wraps
from sanic import response
from sanic.request import Request


class SingletonAsyncRateLimiter:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.rate_limits = dict()

    def __call__(self, seconds: int, limit: int):
        def decorator(f):
            @wraps(f)
            async def decorated_function(request: Request, *args, **kwargs):
                async with self._lock:
                    key = (request.url, request.remote_addr)
                    current_time = asyncio.get_event_loop().time()
                    last_time, count = self.rate_limits.get(key, (0, 0))

                    if current_time - last_time > seconds:
                        self.rate_limits[key] = (current_time, 1)
                    else:
                        if count >= limit:
                            return response.json({"code": 429, "message": "Too Many Requests"}, status=429)
                        self.rate_limits[key] = (last_time, count + 1)

                return await f(request, *args, **kwargs)
            return decorated_function
        return decorator


rate_limiter = SingletonAsyncRateLimiter()
