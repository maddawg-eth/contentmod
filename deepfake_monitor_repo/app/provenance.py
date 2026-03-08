from __future__ import annotations


def check_provenance(video_path: str) -> dict:
    return {
        "has_content_credentials": False,
        "verified": False,
        "note": "C2PA verification not configured in this MVP.",
        "video_path": video_path,
    }
