from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a2wsgi import ASGIMiddleware  # noqa: E402

from app.main import app as fastapi_app  # noqa: E402

_wsgi_application = None
_wsgi_application_pid = None


def application(environ, start_response):
    global _wsgi_application, _wsgi_application_pid

    pid = os.getpid()
    if _wsgi_application is None or _wsgi_application_pid != pid:
        _wsgi_application = ASGIMiddleware(fastapi_app)
        _wsgi_application_pid = pid

    return _wsgi_application(environ, start_response)
