import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.services.auth import decode_token

logger = logging.getLogger(__name__)

PUBLIC_PREFIXES = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/",
    "/api/v1/quotes/indices",
    "/api/v1/search/trending",
}

PUBLIC_EXACT = {"/", "/health"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        is_public = path in PUBLIC_EXACT or any(
            path.startswith(p) for p in PUBLIC_PREFIXES
        )

        if not is_public and path.startswith("/api/v1/"):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = decode_token(token)
                if payload and payload.get("type") == "access":
                    request.state.user = {
                        "id": payload.get("user_id"),
                        "email": payload.get("sub"),
                        "plan": payload.get("plan", "FREE"),
                    }
                else:
                    request.state.user = None
            else:
                api_key = request.headers.get("X-API-Key", "")
                if api_key:
                    request.state.user = {"api_key": api_key, "plan": "DEVELOPER"}
                else:
                    request.state.user = None
        else:
            request.state.user = None

        response = await call_next(request)
        return response
