import redis

r = redis.Redis(host='127.0.0.1', port=6379)
try:
    r.ping()
    print("Connected to Redis!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")
