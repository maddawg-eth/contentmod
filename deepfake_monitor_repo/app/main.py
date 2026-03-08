from __future__ import annotations

import json
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.adapters.youtube import search_youtube
from app.adapters.x import search_x
from app.config import settings
from app.crud import create_analysis_placeholder, create_or_get_candidate, create_reference_media, get_active_profile, get_candidate, list_candidates_with_latest_analysis, upsert_single_profile
from app.db import get_db
from app.media import candidate_media_dir, reference_media_dir, save_upload
from app.models import AnalysisResult, CandidateVideo, MonitoredProfile
from app.schemas import DiscoverRequest, ManualCandidateCreate, ProfileCreate, ReviewUpdate
from app.tasks import run_candidate_analysis

app = FastAPI(title="Deepfake Monitor")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    profile = get_active_profile(db)
    candidates = list_candidates_with_latest_analysis(db)
    rows = []
    for candidate in candidates:
        latest = sorted(candidate.analyses, key=lambda a: a.created_at, reverse=True)[0] if candidate.analyses else None
        rows.append({"candidate": candidate, "latest": latest})
    return templates.TemplateResponse("dashboard.html", {"request": request, "profile": profile, "rows": rows})


@app.get("/candidates/{candidate_id}", response_class=HTMLResponse)
def candidate_detail(candidate_id: int, request: Request, db: Session = Depends(get_db)):
    candidate = get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    analyses = sorted(candidate.analyses, key=lambda a: a.created_at, reverse=True)
    return templates.TemplateResponse("candidate_detail.html", {"request": request, "candidate": candidate, "analyses": analyses})


@app.post("/api/profile")
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    profile = upsert_single_profile(db, payload.full_name, payload.aliases, payload.known_handles, payload.description)
    return {"id": profile.id, "full_name": profile.full_name}


@app.post("/api/profile/reference")
def upload_reference_media(
    media_type: str = Form(...),
    label: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    profile = get_active_profile(db)
    if profile is None:
        raise HTTPException(status_code=400, detail="Create a profile first")
    if media_type not in {"image", "audio"}:
        raise HTTPException(status_code=400, detail="media_type must be image or audio")
    dest = save_upload(file.file, reference_media_dir(profile.id), file.filename)
    item = create_reference_media(db, profile.id, media_type, str(dest), label)
    return {"id": item.id, "file_path": item.file_path}


@app.post("/api/discover")
async def discover(payload: DiscoverRequest, db: Session = Depends(get_db)):
    profile = get_active_profile(db)
    if profile is None:
        raise HTTPException(status_code=400, detail="Create a profile first")

    queries = [profile.full_name] + [a.alias for a in profile.aliases] + [h.handle for h in profile.handles]
    queries = list(dict.fromkeys([q.strip() for q in queries if q.strip()]))
    created = []
    for query in queries:
        if "youtube" in payload.platforms:
            for item in await search_youtube(query, payload.max_candidates_per_query):
                c = create_or_get_candidate(db, profile_id=profile.id, source_query=query, **item)
                created.append(c.id)
        if "x" in payload.platforms:
            for item in await search_x(query, payload.max_candidates_per_query):
                c = create_or_get_candidate(db, profile_id=profile.id, source_query=query, **item)
                created.append(c.id)
    return {"candidate_ids": sorted(set(created)), "count": len(set(created))}


@app.post("/api/candidates/manual")
def add_manual_candidate(payload: ManualCandidateCreate, db: Session = Depends(get_db)):
    profile = get_active_profile(db)
    if profile is None:
        raise HTTPException(status_code=400, detail="Create a profile first")
    candidate = create_or_get_candidate(
        db,
        profile_id=profile.id,
        platform=payload.platform,
        external_id=payload.external_id,
        url=str(payload.url),
        title=payload.title,
        description=payload.description,
        account_name=payload.account_name,
        posted_at_raw=payload.posted_at_raw,
        source_query="manual",
    )
    return {"id": candidate.id}


@app.post("/api/candidates/{candidate_id}/upload")
def upload_candidate_media(candidate_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    candidate = db.get(CandidateVideo, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    dest = save_upload(file.file, candidate_media_dir(candidate.id), file.filename)
    candidate.media_path = str(dest)
    db.commit()
    return {"candidate_id": candidate.id, "media_path": candidate.media_path}


@app.post("/api/candidates/{candidate_id}/analyze")
def analyze_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(CandidateVideo, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    analysis = create_analysis_placeholder(db, candidate_id)
    async_result = run_candidate_analysis.delay(candidate.id, analysis.id)
    analysis.task_id = async_result.id
    db.commit()
    return {"analysis_id": analysis.id, "task_id": async_result.id}


@app.post("/api/candidates/{candidate_id}/review")
def update_review(candidate_id: int, payload: ReviewUpdate, db: Session = Depends(get_db)):
    candidate = db.get(CandidateVideo, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.review_status = payload.review_status
    candidate.review_notes = payload.review_notes
    db.commit()
    return {"ok": True}


@app.post("/dashboard/profile")
def dashboard_profile(
    full_name: str = Form(...),
    aliases: str = Form(""),
    handles: str = Form(""),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
):
    alias_list = [a.strip() for a in aliases.splitlines() if a.strip()]
    handle_list = [h.strip() for h in handles.splitlines() if h.strip()]
    upsert_single_profile(db, full_name, alias_list, handle_list, description)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/dashboard/manual-candidate")
def dashboard_manual_candidate(
    platform: str = Form(...),
    external_id: str = Form(...),
    url: str = Form(...),
    title: str | None = Form(None),
    description: str | None = Form(None),
    account_name: str | None = Form(None),
    db: Session = Depends(get_db),
):
    profile = get_active_profile(db)
    if profile is None:
        raise HTTPException(status_code=400, detail="Create a profile first")
    create_or_get_candidate(
        db,
        profile_id=profile.id,
        platform=platform,
        external_id=external_id,
        url=url,
        title=title,
        description=description,
        account_name=account_name,
        source_query="manual",
    )
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/dashboard/discover")
async def dashboard_discover(platforms: list[str] = Form([]), max_candidates_per_query: int = Form(10), db: Session = Depends(get_db)):
    profile = get_active_profile(db)
    if profile is None:
        raise HTTPException(status_code=400, detail="Create a profile first")
    if not platforms:
        platforms = ["youtube", "x"]
    payload = DiscoverRequest(platforms=platforms, max_candidates_per_query=max_candidates_per_query)
    await discover(payload, db)
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/dashboard/candidates/{candidate_id}/upload")
def dashboard_upload_candidate(candidate_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    upload_candidate_media(candidate_id, file, db)
    return RedirectResponse(url=f"/candidates/{candidate_id}", status_code=303)


@app.post("/dashboard/candidates/{candidate_id}/analyze")
def dashboard_analyze_candidate(candidate_id: int, db: Session = Depends(get_db)):
    analyze_candidate(candidate_id, db)
    return RedirectResponse(url=f"/candidates/{candidate_id}", status_code=303)


@app.post("/dashboard/candidates/{candidate_id}/review")
def dashboard_update_review(candidate_id: int, review_status: str = Form(...), review_notes: str | None = Form(None), db: Session = Depends(get_db)):
    update_review(candidate_id, ReviewUpdate(review_status=review_status, review_notes=review_notes), db)
    return RedirectResponse(url=f"/candidates/{candidate_id}", status_code=303)
