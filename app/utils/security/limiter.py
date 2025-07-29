from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config.env import get_settings
from app.utils.middleware.dependancies import get_optional_user_id
from fastapi import Request, Depends
from typing import Optional
from uuid import UUID



def jwt_user_or_ip_key(
    request: Request,
    user_id: Optional[UUID] = Depends(get_optional_user_id)
) -> str:
    """
    Returns the user_id string from the JWT if available,
    otherwise falls back to the client's IP address.
    """
    if user_id:
        return str(user_id)  # Use the authenticated user's ID
    return get_remote_address(request) # Fallback for anonymous users

setting = get_settings()
LIMITER = Limiter(
    key_func=jwt_user_or_ip_key,
    storage_uri=setting.REDIS_URL,
    default_limits=[setting.RATE_LIMIT_MINUTE, setting.RATE_LIMIT_HOUR, setting.RATE_LIMIT_SECOND] # <-- SET DEFAULT RATES HERE
)