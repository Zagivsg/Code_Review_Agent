# Redis queue for async tasks
import redis
from rq import Queue
import os

# Connect to Redis using the hostname provided by Docker Compose
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
conn = redis.Redis(host=REDIS_HOST, port=6379)

# Create a default queue for handling review tasks
queue = Queue(connection=conn)
