"""Timezone-aware timestamps shared by readers and trade diagnostics."""
from datetime import datetime


def timestamp(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Dates require an explicit timezone")
    return result
