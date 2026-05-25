"""
scrapers/steam.py
=================
SteamScraper: enrich GameData dengan harga, review, dan requirements dari Steam.
"""

from utils.helpers import strip_html
from .base import BaseScraper


class SteamScraper(BaseScraper):
    STORE  = "https://store.steampowered.com/api"
    SEARCH = "https://store.steampowered.com/api/storesearch"

    def __init__(self):
        super().__init__(delay=1.0)

    def _find_appid(self, title: str):
        items = self.get(self.SEARCH, {"term": title, "cc": "ID", "l": "english"})
        if not items:
            return None
        candidates = items.get("items") or []
        if not candidates:
            return None
        title_lower = title.lower().strip()
        # 1) Exact match
        for item in candidates[:5]:
            if (item.get("name") or "").lower().strip() == title_lower:
                return item.get("id")
        # 2) Substring match
        for item in candidates[:5]:
            cname = (item.get("name") or "").lower().strip()
            if title_lower in cname or cname in title_lower:
                return item.get("id")
        # 3) Fallback top result
        return candidates[0].get("id")

    def enrich(self, g):
        appid = getattr(g, "steam_appid", None) or self._find_appid(g.title)
        if not appid:
            return g
        d = self.get(f"{self.STORE}/appdetails", {"appids": appid, "cc": "ID", "l": "english"})
        if not d:
            return g
        app = (d.get(str(appid)) or {})
        if not app.get("success"):
            return g

        data  = app["data"]
        price = data.get("price_overview", {})
        g.steam_appid     = appid
        g.steam_is_free   = data.get("is_free", False)
        g.steam_price_usd = price.get("final_formatted", "")

        rv = self.get(
            f"https://store.steampowered.com/appreviews/{appid}",
            {"json": 1, "language": "all", "num_per_page": 0},
        )
        g.steam_review_summary = (rv or {}).get("query_summary", {}).get("review_score_desc", "")
        g.source_steam = True

        if not g.description:
            g.description = strip_html(data.get("detailed_description", ""))

        steam_header = data.get("header_image", "")
        if steam_header:
            g.cover_image = steam_header
        elif not g.cover_image:
            g.cover_image = steam_header

        if not g.metacritic_score:
            g.metacritic_score = data.get("metacritic", {}).get("score")

        reqs = data.get("pc_requirements", {})
        if isinstance(reqs, dict):
            g.pc_minimum     = strip_html(reqs.get("minimum", ""))
            g.pc_recommended = strip_html(reqs.get("recommended", ""))

        if not g.age_rating:
            raw_age = str(data.get("required_age", "")).strip()
            g.age_rating = raw_age if raw_age and raw_age != "0" else ""

        return g
