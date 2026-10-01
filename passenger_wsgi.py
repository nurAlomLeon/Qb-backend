from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a2wsgi import ASGIMiddleware  # noqa: E402

from app.main import app as fastapi_app  # noqa: E402

application = ASGIMiddleware(fastapi_app)
