from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple


class RateLimitMiddleware:
    def __init__(
        self,
        app,
        *,
        per_minute: int = 120,
        auth_per_minute: int = 20,
    ) -> None:
        self.app = app
        self.per_minute = per_minute
        self.auth_per_minute = auth_per_minute
        self._hits: Dict[Tuple[str, bool], Deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        is_auth = path.startswith("/api/v1/auth")
        limit = self.auth_per_minute if is_auth else self.per_minute
        client = (scope.get("client") or ("unknown", 0))[0]
        key = (client, is_auth)

        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()

        if len(bucket) >= limit:
            body = json.dumps(
                {
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests, please slow down.",
                    }
                }
            ).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                        (b"retry-after", b"60"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        bucket.append(now)
        await self.app(scope, receive, send)
