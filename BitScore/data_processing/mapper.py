"""
processor/mapper.py
-------------------
Mapping dari raw GameData dict → dict siap pakai oleh UI.
"""

from config.theme import (
    META_GREEN, META_YELLOW, META_RED, TEXT_DIM, FREE_GREEN
)


# ── Genre color map ───────────────────────────────────────────────────────────

_GENRE_COLOR_MAP = {
    "RPG":        "#3a1e6e",
    "Action":     "#6e1e1e",
    "Adventure":  "#1e4a6e",
    "Horror":     "#1a0a0a",
    "Simulation": "#1e4a2e",
    "Racing":     "#4a2e1e",
    "Sports":     "#1e3a5e",
    "Arcade":     "#4a1e4a",
    "Casual":     "#2e4a1e",
}


def genre_color(genres: list) -> str:
    for g in genres:
        if g in _GENRE_COLOR_MAP:
            return _GENRE_COLOR_MAP[g]
    return "#2a1040"


# ── Score color helpers ───────────────────────────────────────────────────────

def meta_color(score) -> str:
    if score is None: return TEXT_DIM
    if score >= 85:   return META_GREEN
    if score >= 70:   return META_YELLOW
    return META_RED


def review_color(review: str) -> str:
    r = review.lower()
    if "overwhelmingly positive" in r or "very positive" in r:
        return META_GREEN
    if "positive" in r: return META_GREEN
    if "mixed" in r:    return META_YELLOW
    if "negative" in r: return META_RED
    return TEXT_DIM


# ── Main mapper ───────────────────────────────────────────────────────────────

def map_game(item: dict, idx: int) -> dict:
    genres    = item.get("genres") or []
    rawg      = item.get("rawg_rating")
    meta      = item.get("metacritic_score")
    rating    = round(float(rawg), 2) if rawg else (
                round(float(meta) / 20, 2) if meta else 0.0)

    price_usd = item.get("steam_price_usd") or ""
    is_free   = item.get("steam_is_free", False)
    price     = "FREE" if is_free else (price_usd if price_usd else "N/A")

    rel = item.get("release_date") or ""

    return {
        "id"            : idx + 1,
        "title"         : item.get("title", "Unknown"),
        "description"   : item.get("description", ""),
        "genres"        : genres,
        "platforms"     : item.get("platforms") or [],
        "developer"     : ", ".join(item.get("developers") or []) or "Unknown",
        "publisher"     : ", ".join(item.get("publishers") or []),
        "tags"          : item.get("tags") or [],
        "rating"        : rating,
        "metacritic"    : meta,
        "rawg_count"    : item.get("rawg_rating_count") or 0,
        "cover_url"     : item.get("cover_image") or "",
        "screenshots"   : item.get("screenshots") or [],
        "price"         : price,
        "is_free"       : is_free,
        "deal_price"    : item.get("deal_price") or "",
        "deal_savings"  : item.get("deal_savings") or "",
        "review"        : item.get("steam_review_summary") or "",
        "year"          : rel[:4] if rel else "?",
        "release_date"  : rel,
        "website"       : item.get("website") or "",
        "age_rating"    : item.get("age_rating") or "",
        "pc_minimum"    : item.get("pc_minimum") or "",
        "pc_recommended": item.get("pc_recommended") or "",
        "color"         : genre_color(genres),
    }
