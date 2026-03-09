from __future__ import annotations

from typing import Any

from app.config import settings


async def search_tiktok_candidates(person, max_per_query: int = 10) -> list[dict[str, Any]]:
    # Intentionally conservative:
    # only use approved/authorized access you configure later.
    if not settings.enable_tiktok or not settings.tiktok_access_token:
        return []
    return []
