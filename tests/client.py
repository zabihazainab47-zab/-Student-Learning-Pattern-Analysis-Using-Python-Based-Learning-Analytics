"""
client.py — Patched Starlette TestClient compatible with httpx >= 0.28.0
Bypasses the obsolete `app=self.app` parameter in Starlette 0.36.3 with httpx 0.28.1.
"""

from starlette.testclient import (
    TestClient as StarletteTestClient,
    _AsyncBackend,
    _is_asgi3,
    _TestClientTransport,
    _WrapASGI2,
)


class TestClient(StarletteTestClient):
    def __init__(
        self,
        app,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: dict = None,
        cookies=None,
        headers=None,
        follow_redirects: bool = True,
    ) -> None:
        self.async_backend = _AsyncBackend(
            backend=backend, backend_options=backend_options or {}
        )
        if _is_asgi3(app):
            asgi_app = app
        else:
            asgi_app = _WrapASGI2(app)

        self.app = asgi_app
        self.app_state: dict = {}
        transport = _TestClientTransport(
            self.app,
            portal_factory=self._portal_factory,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
            app_state=self.app_state,
        )
        if headers is None:
            headers = {}
        headers.setdefault("user-agent", "testclient")
        self.portal = None

        # Call httpx.Client.__init__ directly, omitting deprecated app argument
        super(StarletteTestClient, self).__init__(
            base_url=base_url,
            headers=headers,
            transport=transport,
            follow_redirects=follow_redirects,
            cookies=cookies,
        )
