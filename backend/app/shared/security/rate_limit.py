"""
Small fixed-window rate limiter for public (no login) endpoints.

Counters live in Redis (shared by every API worker). When Redis is not
reachable the limiter falls back to an in-process counter, so the page keeps
working in development without Docker; Redis is retried after a cool-down.
"""
import logging
import threading
import time

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

REDIS_RETRY_SECONDS = 30


class RateLimiter:
    def __init__(self, redis_url: str | None, prefix: str = "ratelimit"):
        self.redis_url = redis_url
        self.prefix = prefix
        self._redis = None
        self._redis_down_until = 0.0
        self._memory: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    # -------------------------------------------------------------- backends

    def _get_redis(self):
        if not self.redis_url or time.monotonic() < self._redis_down_until:
            return None
        if self._redis is None:
            import redis  # installed with Celery

            self._redis = redis.Redis.from_url(self.redis_url, socket_timeout=0.3, socket_connect_timeout=0.3)
        return self._redis

    def _hit_redis(self, client, key: str, window: int) -> int:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window + 5)  # key name already contains the window
        return count

    def _hit_memory(self, key: str, window: int) -> int:
        now = time.monotonic()
        with self._lock:
            count, reset_at = self._memory.get(key, (0, now + window))
            if now >= reset_at:
                count, reset_at = 0, now + window
            count += 1
            self._memory[key] = (count, reset_at)
            if len(self._memory) > 50_000:  # drop expired keys now and then
                self._memory = {k: v for k, v in self._memory.items() if v[1] > now}
            return count

    # -------------------------------------------------------------- public API

    def hit(self, bucket: str, identity: str, limit: int, window: int) -> bool:
        """Counts one request; returns False when the limit is exceeded."""
        key = f"{self.prefix}:{bucket}:{identity}:{int(time.time() // window)}"
        client = self._get_redis()
        if client is not None:
            try:
                return self._hit_redis(client, key, window) <= limit
            except Exception as exc:  # Redis down: degrade, do not break the page
                logger.warning("Rate limiter: Redis unavailable (%s), using in-memory counters", exc.__class__.__name__)
                self._redis_down_until = time.monotonic() + REDIS_RETRY_SECONDS
        return self._hit_memory(key, window) <= limit

    def reset(self) -> None:
        with self._lock:
            self._memory.clear()


limiter = RateLimiter(settings.RATE_LIMIT_REDIS_URL)


def client_ip(request: Request) -> str:
    # Behind a reverse proxy, configure it to set the real client address
    # (uvicorn --proxy-headers); X-Forwarded-For is not trusted blindly here.
    return request.client.host if request.client else "unknown"


def rate_limit(bucket: str, limit_setting: str, window_setting: str):
    """FastAPI dependency: 429 when the caller's IP exceeds the configured limit."""

    def dependency(request: Request) -> None:
        limit = getattr(settings, limit_setting)
        window = getattr(settings, window_setting)
        if limit <= 0:
            return
        if not limiter.hit(bucket, client_ip(request), limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çok fazla istek gönderildi. Lütfen birkaç dakika sonra tekrar deneyin.",
                headers={"Retry-After": str(window)},
            )

    return dependency
