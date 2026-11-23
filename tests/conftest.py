import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "assumption-hunter"
SCRIPTS = SKILL / "scripts"
INITIAL = SKILL / "assets" / "assumptions.example.json"
UPDATED = ROOT / "examples" / "updated.json"


@pytest.fixture
def initial():
    return json.loads(INITIAL.read_text(encoding="utf-8"))


@pytest.fixture
def updated():
    return json.loads(UPDATED.read_text(encoding="utf-8"))
