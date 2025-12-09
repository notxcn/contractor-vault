"""
Rate limiter configuration for Contractor Vault.
Uses slowapi to implement request rate limiting.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance using IP address as the key
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "generate_token": "10/minute",   # Token generation: 10 per minute
    "claim_session": "30/minute",    # Session claims: 30 per minute  
    "store_session": "5/minute",     # Session storage: 5 per minute
    "default": "100/minute",         # Default: 100 per minute
}
