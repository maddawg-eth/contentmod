from __future__ import annotations

from typing import Any

from app.adapters.x import search_x


def _build_queries(person) -> list[str]:
    queries: list[str] = []

    for value in [person.full_name] + (person.aliases or []):
        if not value:
            continue
        queries.append(f'"{value}" has:videos -is:retweet')
        queries.append(f'"{value}" (AI OR deepfake OR fake) has:videos -is:retweet')

    for acct in person.reference_accounts or []:
        handle = (acct or "").lstrip("@").strip()
        if handle:
            queries.append(f"from:{handle} has:videos")
            queries.append(f"to:{handle} has:videos")
            queries.append(f"@{handle} has:videos")

    return list(dict.fromkeys(queries))


async def search_x_candidates(person, max_per_query: int = 25) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in _build_queries(person)[:25]:
        items = await search_x(q, max_results=max_per_query)
        for item in items:
            out.append(
                {
                    "platform": "x",
                    "external_id": item["video_id"],
                    "url": item["url"],
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "account_name": item.get("account_name"),
                    "posted_at": item.get("posted_at"),
                    "discovery_reason": "query_match",
                    "raw_metrics": {},
                    "raw_payload": item,
                }
            )
    return out
