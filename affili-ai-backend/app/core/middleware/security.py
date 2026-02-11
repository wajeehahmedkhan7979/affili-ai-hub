"""
Security middleware for sensitive operational endpoints.
Phase 11: Observability Hardening

Protects /metrics and other operational endpoints from public access.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request
import ipaddress
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MetricsSecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to restrict access to /metrics endpoint.
    
    Only allows access from IPs listed in METRICS_ALLOWED_IPS.
    Default: localhost only.
    """
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            client_ip = request.client.host
            
            if not self.is_ip_allowed(client_ip):
                logger.warning(
                    f"Blocked access to /metrics from unauthorized IP: {client_ip}",
                    extra={
                        "event": "security_metrics_blocked",
                        "ip": client_ip
                    }
                )
                return Response("Forbidden", status_code=403)
                
        return await call_next(request)

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in the allowed list (supports CIDR)."""
        if not ip:
            return False
            
        try:
            client_ip = ipaddress.ip_address(ip)
            
            for allowed in settings.METRICS_ALLOWED_IPS:
                if '/' in allowed:
                    # CIDR notation
                    if client_ip in ipaddress.ip_network(allowed):
                        return True
                else:
                    # Exact match
                    if client_ip == ipaddress.ip_address(allowed):
                        return True
            return False
            
        except ValueError:
            # Invalid IP format
            return False
