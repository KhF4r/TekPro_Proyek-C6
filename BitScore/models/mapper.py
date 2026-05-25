"""
models/mapper.py
================
Fungsi konversi: dict mentah JSON → dict UI yang siap ditampilkan.
"""

import json
from pathlib import Path
from config.theme import genre_bg


def map_item(item: dict, idx: int) -> dict:
    """Map satu record JSON ke format UI."""
    genres  = item.get("genres") or []
    rawg    = item.get("rawg_rating")
    meta    = item.get("metacritic_score")
    rating  = round(float(rawg), 2) if rawg else (round(float(meta) / 20, 2) if meta else 0.0)
    price_u = item.get("steam_price_usd") or ""
    is_free = item.get("steam_is_free", False)
    price   = "FREE" if is_free else (price_u if price_u else "N/A")
    rel     = item.get("release_date") or ""

    return {
        "id":             idx + 1,
        "title":          item.get("title", "Unknown"),
        "slug":           item.get("slug", ""),
        "description":    item.get("description", ""),
        "genres":         genres,
        "platforms":      item.get("platforms") or [],
        "developer":      ", ".join(item.get("developers") or []) or "Unknown",
        "publisher":      ", ".join(item.get("publishers") or []),
        "tags":           item.get("tags") or [],
        "rating":         rating,
        "metacritic":     meta,
        "rawg_count":     item.get("rawg_rating_count") or 0,
        "cover_url":      item.get("cover_image") or "",
        "screenshots":    item.get("screenshots") or [],
        "price":          price,
        "is_free":        is_free,
        "deal_price":     item.get("deal_price") or "",
        "deal_savings":   item.get("deal_savings") or "",
        "review":         item.get("steam_review_summary") or "",
        "year":           rel[:4] if rel else "?",
        "release_date":   rel,
        "website":        item.get("website") or "",
        "age_rating":     item.get("age_rating") or "",
        "pc_minimum":     item.get("pc_minimum") or "",
        "pc_recommended": item.get("pc_recommended") or "",
        "steam_appid":    item.get("steam_appid"),
        "color":          genre_bg(genres),
    }


def load_json(path) -> list:
    """Baca file JSON dan konversi ke list UI dict."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [map_item(item, i) for i, item in enumerate(data)]


def games_to_ui(games) -> list:
    """Konversi list GameData ke list UI dict."""
    return [map_item(g.to_dict(), i) for i, g in enumerate(games)]
