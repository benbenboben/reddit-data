import redis


class RedisQueue:

    def __init__(self, name,  **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.db = redis.Redis(**redis_kwargs)
        self.key = f'queue:{name}'

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.db.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.db.blpop(self.key, timeout=timeout)
        else:
            item = self.db.lpop(self.key)

        if item:
            item = item[1]

        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)
