"""
Contractor Vault - Audit Middleware
Automatic request logging for SOC2 compliance
"""
import logging
import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all requests to sensitive endpoints.
    
    SOC2 Requirements:
    - Captures real IP address (handles proxies)
    - Logs request metadata for forensics
    - Tracks endpoints: /generate, /revoke, /claim
    
    Design Notes:
    - IP extraction considers X-Forwarded-For and X-Real-IP headers
    - Uses starlette.state for passing audit context to route handlers
    """
    
    # Endpoints that require audit logging
    AUDIT_PATHS = [
        "/api/access/generate",
        "/api/access/revoke",
        "/api/access/claim",
        "/api/credentials",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        """
        Process request and attach audit metadata.
        
        Extracts:
        - Real client IP (proxy-aware)
        - User agent
        - Request timestamp
        - Request path and method
        """
        # Extract client IP (proxy-aware)
        client_ip = self._get_client_ip(request)
        
        # Extract user agent for metadata
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Attach audit context to request state for use in route handlers
        request.state.audit_context = {
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request_time": time.time(),
            "path": request.url.path,
            "method": request.method,
        }
        
        # Check if this path should be logged
        should_audit = any(
            request.url.path.startswith(path) 
            for path in self.AUDIT_PATHS
        )
        
        if should_audit:
            logger.info(
                f"AUDIT_REQUEST: {request.method} {request.url.path} "
                f"from {client_ip} UA={user_agent[:50]}"
            )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        if should_audit:
            logger.info(
                f"AUDIT_RESPONSE: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )
        
        # Add audit headers to response
        response.headers["X-Request-ID"] = str(id(request))
        response.headers["X-Request-Duration"] = f"{duration:.3f}"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract real client IP address, handling proxy headers.
        
        Priority:
        1. X-Forwarded-For (first IP in chain)
        2. X-Real-IP
        3. Direct client IP
        
        Security Note:
        - X-Forwarded-For can be spoofed if not behind trusted proxy
        - In production, configure trusted proxies appropriately
        """
        # X-Forwarded-For contains comma-separated list of IPs
        # Format: "client, proxy1, proxy2"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first (original client) IP
            client_ip = forwarded_for.split(",")[0].strip()
            return client_ip
        
        # X-Real-IP is set by some proxies (nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


def get_audit_context(request: Request) -> dict:
    """
    Helper to retrieve audit context from request state.
    
    Usage in route handlers:
        context = get_audit_context(request)
        ip = context["client_ip"]
    """
    if hasattr(request.state, "audit_context"):
        return request.state.audit_context
    return {
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "path": str(request.url.path),
        "method": request.method,
    }
