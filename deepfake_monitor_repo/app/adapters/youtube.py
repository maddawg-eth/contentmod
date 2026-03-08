from __future__ import annotations

from typing import Any
import httpx
from app.config import settings

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


async def search_youtube(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    if not settings.youtube_api_key:
        return []

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": settings.youtube_api_key,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(YOUTUBE_SEARCH_URL, params=params)
        r.raise_for_status()
        data = r.json()

    ids = [item["id"]["videoId"] for item in data.get("items", []) if item.get("id", {}).get("videoId")]
    if not ids:
        return []

    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(ids),
        "key": settings.youtube_api_key,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(YOUTUBE_VIDEOS_URL, params=params)
        r.raise_for_status()
        videos = r.json().get("items", [])

    out: list[dict[str, Any]] = []
    for v in videos:
        snippet = v.get("snippet", {})
        vid = v.get("id")
        if not vid:
            continue
        out.append(
            {
                "platform": "youtube",
                "external_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "account_name": snippet.get("channelTitle"),
                "posted_at_raw": snippet.get("publishedAt"),
            }
        )
    return out
