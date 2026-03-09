def compute_viral_score(metrics: dict) -> float:
    views = float(metrics.get("views", 0) or 0)
    likes = float(metrics.get("likes", 0) or 0)
    shares = float(metrics.get("shares", 0) or 0)
    comments = float(metrics.get("comments", 0) or 0)
    age_hours = max(float(metrics.get("age_hours", 24) or 24), 1.0)

    engagement_velocity = (likes + 2 * shares + comments) / age_hours
    reach_velocity = views / age_hours

    raw = 0.6 * min(reach_velocity / 5000.0, 1.0) + 0.4 * min(engagement_velocity / 500.0, 1.0)
    return round(min(raw, 1.0), 4)
