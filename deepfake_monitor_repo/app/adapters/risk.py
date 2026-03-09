def compute_final_risk(
    title: str = "",
    body_text: str = "",
    transcript: str = "",
    face_match_score: float | None = None,
    voice_match_score: float | None = None,
    synthetic_voice_score: float | None = None,
    viral_score: float = 0.0,
) -> dict:
    text_blob = " ".join([title or "", body_text or "", transcript or ""]).lower()

    keyword_score = 0.0
    for term in ["deepfake", "ai", "fake video", "cloned voice", "synthetic"]:
        if term in text_blob:
            keyword_score = min(keyword_score + 0.15, 0.45)

    face_component = min(max(face_match_score or 0.0, 0.0), 1.0)
    voice_component = min(max(voice_match_score or 0.0, 0.0), 1.0)
    synthetic_voice_component = min(max(synthetic_voice_score or 0.0, 0.0), 1.0)
    viral_component = min(max(viral_score or 0.0, 0.0), 1.0)

    score = (
        0.30 * face_component
        + 0.15 * voice_component
        + 0.20 * synthetic_voice_component
        + 0.20 * keyword_score
        + 0.15 * viral_component
    )

    if score >= 0.80:
        label = "high"
    elif score >= 0.50:
        label = "medium"
    else:
        label = "low"

    should_alert = score >= 0.80 or (score >= 0.65 and viral_component >= 0.60)

    return {
        "score": round(score, 4),
        "label": label,
        "should_alert": should_alert,
    }
