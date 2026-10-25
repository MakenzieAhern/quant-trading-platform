"""Bound untrusted HTTP bodies before JSON parsing, including chunked requests."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestBodyLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        max_bytes: int = 65536,
        allowed_origins: tuple[str, ...] = ("http://localhost:5173",),
    ) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.allowed_origins = allowed_origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        origin = dict(scope.get("headers", [])).get(b"origin")
        if (
            scope["method"] not in {"GET", "HEAD", "OPTIONS"}
            and origin is not None
            and origin.decode("latin-1") not in self.allowed_origins
        ):
            await JSONResponse({"detail": "origin not allowed"}, status_code=403)(
                scope, receive, send
            )
            return
        body = bytearray()
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                await JSONResponse({"detail": "request body too large"}, status_code=413)(
                    scope, receive, send
                )
                return
            body.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break

        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay, send)
