from __future__ import annotations

from typing import Any
import httpx
from app.config import settings

X_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"


async def search_x(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    if not settings.x_bearer_token:
        return []

    headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}
    params = {
        "query": f'(\"{query}\") has:videos -is:retweet',
        "max_results": min(max_results, 100),
        "tweet.fields": "created_at,author_id,text",
        "expansions": "attachments.media_keys",
        "media.fields": "preview_image_url,url,type",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(X_SEARCH_URL, headers=headers, params=params)
        r.raise_for_status()
        payload = r.json()

    media_by_key = {m["media_key"]: m for m in payload.get("includes", {}).get("media", [])}
    out: list[dict[str, Any]] = []
    for item in payload.get("data", []):
        media_keys = item.get("attachments", {}).get("media_keys", [])
        has_video = any(media_by_key.get(k, {}).get("type") == "video" for k in media_keys)
        if not has_video:
            continue
        tweet_id = item["id"]
        out.append(
            {
                "platform": "x",
                "external_id": tweet_id,
                "url": f"https://x.com/i/web/status/{tweet_id}",
                "title": item.get("text", "")[:120],
                "description": item.get("text", ""),
                "account_name": item.get("author_id"),
                "posted_at_raw": item.get("created_at"),
            }
        )
    return out
