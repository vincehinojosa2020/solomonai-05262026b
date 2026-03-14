"""
Shared database connection and utility functions for Solomon AI.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Optional
import os
import logging
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger("solomon")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=60000,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    retryWrites=True,
    retryReads=True,
    w='majority'
)
db = client[os.environ['DB_NAME']]


def serialize_doc(doc: dict) -> dict:
    """Remove MongoDB _id and convert datetime objects."""
    if doc is None:
        return None
    result = {k: v for k, v in doc.items() if k != '_id'}
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result


def duration_to_seconds(duration_label: Optional[str], duration_seconds: Optional[int] = None) -> int:
    if duration_seconds is not None:
        try:
            return max(int(duration_seconds), 0)
        except (TypeError, ValueError):
            return 0
    if not duration_label:
        return 0
    parts = [p for p in duration_label.split(':') if p]
    try:
        numbers = list(map(int, parts))
    except ValueError:
        return 0
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    if len(numbers) == 1:
        return numbers[0]
    return 0


# Platform admin accounts
PLATFORM_ADMIN_EMAILS = ["admin@solomon.ai", "admin@abundant.org"]

DEFAULT_TENANT_ID = "abundant-church-001"

ROLES = {
    "platform_admin": 100,
    "church_admin": 50,
    "member": 10,
}
