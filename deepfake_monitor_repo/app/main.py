from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.models import AlertRecipient, Candidate, MonitoredPerson
from app.tasks import run_all_monitors

app = FastAPI(title="Deepfake Monitoring Agent")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    db = SessionLocal()
    try:
        people = db.query(MonitoredPerson).order_by(MonitoredPerson.id.desc()).all()
        candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).limit(100).all()
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "people": people,
                "candidates": candidates,
            },
        )
    finally:
        db.close()


@app.post("/admin/monitor")
def create_monitor(
    full_name: str = Form(...),
    aliases_csv: str = Form(""),
    reference_accounts_csv: str = Form(""),
    reference_images_csv: str = Form(""),
    reference_audio_csv: str = Form(""),
):
    db = SessionLocal()
    try:
        row = MonitoredPerson(
            full_name=full_name.strip(),
            aliases=[x.strip() for x in aliases_csv.split(",") if x.strip()],
            reference_accounts=[x.strip() for x in reference_accounts_csv.split(",") if x.strip()],
            reference_image_paths=[x.strip() for x in reference_images_csv.split(",") if x.strip()],
            reference_audio_paths=[x.strip() for x in reference_audio_csv.split(",") if x.strip()],
            is_active=True,
        )
        db.add(row)
        db.commit()
        return RedirectResponse(url="/dashboard", status_code=303)
    finally:
        db.close()


@app.post("/admin/recipient")
def create_recipient(
    person_id: int = Form(...),
    name: str = Form(...),
    email: str = Form(""),
    phone_e164: str = Form(""),
    send_email: bool = Form(False),
    send_sms: bool = Form(False),
):
    db = SessionLocal()
    try:
        row = AlertRecipient(
            person_id=person_id,
            name=name.strip(),
            email=email.strip() or None,
            phone_e164=phone_e164.strip() or None,
            send_email=send_email,
            send_sms=send_sms,
        )
        db.add(row)
        db.commit()
        return RedirectResponse(url="/dashboard", status_code=303)
    finally:
        db.close()


@app.post("/admin/run-now")
def run_now():
    run_all_monitors.delay()
    return RedirectResponse(url="/dashboard", status_code=303)
