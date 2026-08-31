"""Tool return values must be plain JSON-safe types - the MCP SDK
doesn't know how to encode Decimal or date objects, and neither
does the JSON-RPC wire format they end up on."""

from datetime import date, datetime
from decimal import Decimal


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj
