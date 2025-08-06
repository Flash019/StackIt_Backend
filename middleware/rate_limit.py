from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from time import time

RATE_LIMIT = {}  # IP: [timestamps]
REQUESTS_PER_MINUTE = 30

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        now = time()
        timestamps = RATE_LIMIT.get(ip, [])
        timestamps = [ts for ts in timestamps if now - ts < 60]

        if len(timestamps) >= REQUESTS_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Too many requests")

        timestamps.append(now)
        RATE_LIMIT[ip] = timestamps
        response = await call_next(request)
        return response
