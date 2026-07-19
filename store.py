import time


class Store:
    def __init__(self):
        # key (str) -> value (bytes, or later list/dict/etc for other types)
        self.data = {}
        # key (str) -> absolute expiry time in ms (float), only present if a TTL was set
        self.expires = {}

    def _is_expired(self, key):
        deadline = self.expires.get(key)
        return deadline is not None and time.time() * 1000 >= deadline

    # lazy expiration
    def _expire_if_needed(self, key):
        if key in self.data and self._is_expired(key):
            del self.data[key]
            del self.expires[key]
            return True
        return False

    def set(self, key, value, px=None):
        # px: optional TTL in milliseconds from now
        self.data[key] = value
        if px is not None:
            self.expires[key] = time.time() * 1000 + px
        else:
            # SET without TTL clears any previous expiry
            self.expires.pop(key, None)

    def get(self, key):
        self._expire_if_needed(key)
        return self.data.get(key)  # none if missing or just expired

    def delete(self, key):
        self._expire_if_needed(key)
        existed = key in self.data
        self.data.pop(key, None)
        self.expires.pop(key, None)
        return existed

    def exists(self, key):
        self._expire_if_needed(key)
        return key in self.data

    def expire(self, key, seconds):
        # returns 1 if TTL was set, 0 if key doesn't exist (matches Redis EXPIRE semantics)
        if not self.exists(key):
            return 0
        self.expires[key] = time.time() * 1000 + seconds * 1000
        return 1

    def ttl(self, key):
        # seconds remaining, -1 if no expiry set, -2 if key doesn't exist
        if not self.exists(key):
            return -2
        deadline = self.expires.get(key)
        if deadline is None:
            return -1
        remaining_ms = deadline - time.time() * 1000
        return max(0, int(remaining_ms / 1000))

    def active_expire_cycle(self, sample_size=20):
        import random
        candidates = list(self.expires.keys())
        if not candidates:
            return
        sample = random.sample(candidates, min(sample_size, len(candidates)))
        for key in sample:
            self._expire_if_needed(key)
