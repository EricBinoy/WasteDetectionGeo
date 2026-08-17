from slowapi import Limiter
from slowapi.util import get_remote_address

# Simple IP-based rate limiter: 10 requests/hour/IP on the report submission endpoint.
limiter = Limiter(key_func=get_remote_address)
