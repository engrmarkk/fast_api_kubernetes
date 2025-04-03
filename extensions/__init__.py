from func import get_user_id_from_request
from slowapi import Limiter

# from slowapi.util import get_remote_address
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Redis connection
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST"), port=os.environ.get("REDIS_PORT"), db=0
)

limiter = Limiter(
    key_func=get_user_id_from_request,
    storage_uri=f"redis://{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}",
)
