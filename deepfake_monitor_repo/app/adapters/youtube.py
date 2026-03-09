from __future__ import annotations

from typing import Any

from app.adapters.youtube import search_youtube


def _build_queries(person) -> list[str]:
    queries: list[str] = []

    for value in [person.full_name] + (person.aliases or []):
        if not value:
            continue
        queries.append(f'"{value}"')
        queries.append(f'"{value}" AI')
        queries.append(f'"{value}" deepfake')
        queries.append(f'"{value}" fake video')

    for acct in person.reference_accounts or []:
        if acct:
            queries.append(f'"{acct}"')

    return list(dict.fromkeys(queries))


async def search_youtube_candidates(person, max_per_query: int = 10) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in _build_queries(person)[:20]:
        items = await search_youtube(q, max_results=max_per_query)
        for item in items:
            out.append(
                {
                    "platform": "youtube",
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
