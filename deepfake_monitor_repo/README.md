# Deepfake Monitor

A GitHub-ready, single-user monitoring app for finding and reviewing social-media videos that may be deepfakes associated with one person.

## What it does

- Stores one monitored person's profile, aliases, handles, and reference media
- Searches supported platforms (YouTube and X) by name/alias via official APIs
- Lets you manually add candidate URLs from any platform
- Uploads a lawful local copy of a video for analysis
- Extracts frames, audio, OCR text, and transcript
- Computes identity association and heuristic risk scoring
- Queues analysis jobs with Celery
- Stores results in Postgres
- Provides a reviewer dashboard for triage

## Important limitations

This is a **monitoring and prioritization tool**, not a definitive truth engine.

- The current detector stack is an MVP heuristic ensemble
- It does **not** auto-download videos from platforms
- You should only upload videos you are authorized to store and analyze
- Absence of provenance metadata does not prove a video is fake
- Face/voice models may have licensing constraints depending on what models you swap in

## Stack

- FastAPI
- Jinja2 dashboard
- SQLAlchemy + Postgres
- Celery + Redis
- FFmpeg
- Whisper
- OpenCV
- InsightFace
- Tesseract OCR
- Docker Compose

## Quick start

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Build and run:

```bash
docker compose up --build
```

3. Initialize database:

```bash
docker compose exec api python scripts/init_db.py
```

4. Create your monitored profile:

```bash
docker compose exec api python scripts/seed_profile.py --name "Jane Doe" --alias "J. Doe" --handle "@janedoe"
```

5. Open the dashboard:

```text
http://localhost:8000/dashboard
```

## API overview

### Health

```bash
curl http://localhost:8000/health
```

### Create or update monitored person

```bash
curl -X POST http://localhost:8000/api/profile \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Doe",
    "aliases": ["J. Doe", "Jane A. Doe"],
    "known_handles": ["@janedoe"]
  }'
```

### Discover candidates from APIs

```bash
curl -X POST http://localhost:8000/api/discover \
  -H "Content-Type: application/json" \
  -d '{"platforms": ["youtube", "x"], "max_candidates_per_query": 10}'
```

### Add a manual candidate

```bash
curl -X POST http://localhost:8000/api/candidates/manual \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "tiktok",
    "external_id": "manual-1",
    "url": "https://example.com/video",
    "title": "Possible fake",
    "description": "Found manually"
  }'
```

### Upload media for a candidate

```bash
curl -X POST http://localhost:8000/api/candidates/1/upload \
  -F "file=@/path/to/video.mp4"
```

### Queue analysis

```bash
curl -X POST http://localhost:8000/api/candidates/1/analyze
```

## Directory layout

```text
deepfake_monitor/
  app/
    adapters/
    templates/
    static/
    main.py
    config.py
    db.py
    models.py
    schemas.py
    crud.py
    media.py
    identity.py
    scoring.py
    provenance.py
    tasks.py
  scripts/
    init_db.py
    seed_profile.py
  data/
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
```

## Production hardening ideas

- Add Alembic migrations
- Add a real C2PA verifier
- Add a dedicated voice-clone detector
- Add login/auth if used beyond a single trusted operator
- Add email alerts for high-risk results
- Add evidence export bundles
