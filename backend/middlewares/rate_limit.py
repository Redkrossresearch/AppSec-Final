from collections import defaultdict, deque
from time import time

from flask import jsonify, request


class SimpleRateLimiter:
    def __init__(self, limit=90, window_seconds=60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    def check(self):
        if not request.path.startswith("/api/"):
            return None
        now = time()
        bucket = self.requests[request.remote_addr or "unknown"]
        while bucket and bucket[0] < now - self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return jsonify({"error": "Rate limit exceeded"}), 429
        bucket.append(now)
        return None
