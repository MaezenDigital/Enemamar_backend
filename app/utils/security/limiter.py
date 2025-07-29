from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config.env import get_settings


setting = get_settings()
LIMITER = Limiter(
    key_func=get_remote_address,
    storage_uri=setting.REDIS_URL,
    default_limits=[setting.RATE_LIMIT_MINUTE, setting.RATE_LIMIT_HOUR, setting.RATE_LIMIT_SECOND] # <-- SET DEFAULT RATES HERE
)