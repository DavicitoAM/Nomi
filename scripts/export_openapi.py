"""Run from the repository root using the project virtual environment."""

import json
from pathlib import Path

from app.main import app

Path("docs/api/openapi.json").write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
