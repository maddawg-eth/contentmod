from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.db import SessionLocal
from app.models import MonitoredPerson, MonitorRun
from app.discovery.youtube import search_youtube_candidates
from app.discovery.x import search_x_candidates
from app.discovery.tiktok import search_tiktok_candidates
from app.tasks import analyze_candidate


async def _gather_candidates(person) -> list[dict]:
    results = []
    results.extend(await search_youtube_candidates(person))
    results.extend(await search_x_candidates(person))
    results.extend(await search_tiktok_candidates(person))
    return results


def run_all_monitors_once() -> dict:
    db = SessionLocal()
    run = MonitorRun(status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        people = db.query(MonitoredPerson).filter(MonitoredPerson.is_active == True).all()
        total = 0

        for person in people:
            candidates = asyncio.run(_gather_candidates(person))
            seen = set()

            for c in candidates:
                key = (c["platform"], c["external_id"])
                if key in seen:
                    continue
                seen.add(key)

                analyze_candidate.delay(person.id, c)
                total += 1

        run.status = "finished"
        run.notes = f"Queued {total} candidates"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"queued": total}
    except Exception as e:
        run.status = "failed"
        run.notes = str(e)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise
    finally:
        db.close()
