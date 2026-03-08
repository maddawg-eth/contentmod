from __future__ import annotations

import re


def normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def text_identity_score(full_name: str, aliases: list[str], text_blobs: list[str]) -> float:
    corpus = normalize_text(" ".join(text_blobs))
    names = [full_name] + aliases
    names = [normalize_text(n) for n in names if normalize_text(n)]
    if not names:
        return 0.0
    hits = sum(1 for n in names if n in corpus)
    return min(hits / len(names), 1.0)


def synthetic_face_signal_stub(best_face_match: float) -> float:
    if best_face_match > 0.75:
        return 0.25
    if best_face_match > 0.45:
        return 0.40
    return 0.20


def synthetic_voice_signal_stub(transcript: str) -> float:
    text = normalize_text(transcript)
    if not text:
        return 0.20
    suspicious_markers = ["breaking", "exclusive", "leaked", "i confess", "wire transfer"]
    return 0.45 if any(m in text for m in suspicious_markers) else 0.25


def lipsync_mismatch_stub() -> float:
    return 0.25


def provenance_risk(provenance: dict) -> float:
    if provenance.get("verified"):
        return 0.0
    if provenance.get("has_content_credentials") and not provenance.get("verified"):
        return 0.8
    return 0.4


def account_risk(account_name: str | None) -> float:
    if not account_name:
        return 0.20
    lowered = account_name.lower()
    suspicious = ["fan", "parody", "truth", "viral", "clip", "insider"]
    return 0.35 if any(x in lowered for x in suspicious) else 0.10


def classify(score: float) -> str:
    if score >= 0.70:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


def final_score(identity_match: float, best_face_match: float, transcript: str, provenance: dict, account_name: str | None) -> dict:
    sf = synthetic_face_signal_stub(best_face_match)
    sv = synthetic_voice_signal_stub(transcript)
    lm = lipsync_mismatch_stub()
    pr = provenance_risk(provenance)
    ar = account_risk(account_name)
    score = (
        0.35 * identity_match +
        0.15 * sf +
        0.10 * sv +
        0.10 * lm +
        0.20 * pr +
        0.10 * ar
    )
    score = round(min(max(score, 0.0), 1.0), 4)
    return {
        "score": score,
        "label": classify(score),
        "components": {
            "identity_match": round(identity_match, 4),
            "synthetic_face_signal": round(sf, 4),
            "synthetic_voice_signal": round(sv, 4),
            "lipsync_mismatch": round(lm, 4),
            "provenance_risk": round(pr, 4),
            "account_risk": round(ar, 4),
        },
    }
