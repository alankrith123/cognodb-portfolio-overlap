"""CognoDB driver singleton. Initialized once at import, not per request."""

import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Project root is two levels above this file: backend/app/db.py -> cognodb/
_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

_URI = os.environ.get("COGNODB_URI")
_USER = os.environ.get("COGNODB_USER")
_PASSWORD = os.environ.get("COGNODB_PASSWORD")

if not all([_URI, _USER, _PASSWORD]):
    raise RuntimeError(
        "Missing CognoDB credentials. Set COGNODB_URI, COGNODB_USER, "
        "and COGNODB_PASSWORD in .env"
    )

driver = GraphDatabase.driver(_URI, auth=(_USER, _PASSWORD))


def get_driver():
    return driver


def close_driver():
    driver.close()
