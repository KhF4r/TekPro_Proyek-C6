"""
scraper/steam.py
----------------
Scraper untuk Steam Store API — detail app, harga, review summary,
dan PC requirements.
"""

import re
import logging
from .base import BaseScraper
from .models import GameData

log = logging.getLogger("BitScore")


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", clean).strip()


class SteamScraper(BaseScraper):
    STORE_URL  = "https://store.steampowered.com/api"
    SEARCH_URL = "https://store.steampowered.com/api/storesearch"

    def __init__(self):
        super().__init__(delay=1.0)

    # ── Public API ────────────────────────────────────────────────────────────

    def search(self, query: str, country: str = "ID") -> list:
        data = self.get(self.SEARCH_URL,
                        params={"term": query, "cc": country, "l": "english"})
        return data.get("items", []) if data else []

    def get_app_detail(self, appid: int, country: str = "ID") -> dict | None:
        data = self.get(
            f"{self.STORE_URL}/appdetails",
            params={"appids": appid, "cc": country, "l": "english"},
        )
        if not data:
            return None
        app = data.get(str(appid), {})
        return app.get("data") if app.get("success") else None

    def get_review_summary(self, appid: int) -> str:
        data = self.get(
            f"https://store.steampowered.com/appreviews/{appid}",
            params={"json": 1, "language": "all", "num_per_page": 0},
        )
        return (data.get("query_summary", {}).get("review_score_desc", "")
                if data else "")

    def enrich_game(self, game: GameData) -> GameData:
        results = self.search(game.title)
        if not results:
            return game

        appid = results[0].get("id")
        if not appid:
            return game

        detail = self.get_app_detail(appid)
        if not detail:
            return game

        price              = detail.get("price_overview", {})
        game.steam_appid   = appid
        game.steam_is_free = detail.get("is_free", False)
        game.steam_price_usd = price.get("final_formatted", "")
        game.steam_review_summary = self.get_review_summary(appid)
        game.source_steam  = True

        if not game.description:
            game.description = _strip_html(detail.get("detailed_description", ""))
        if not game.cover_image:
            game.cover_image = detail.get("header_image", "")
        if not game.metacritic_score:
            game.metacritic_score = detail.get("metacritic", {}).get("score")

        game.pc_minimum, game.pc_recommended = self._parse_pc_requirements(detail)

        if not game.age_rating:
            game.age_rating = str(detail.get("required_age", "")) or ""

        return game

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_pc_requirements(self, detail: dict) -> tuple[str, str]:
        reqs = detail.get("pc_requirements", {})
        minimum     = _strip_html(reqs.get("minimum", ""))
        recommended = _strip_html(reqs.get("recommended", ""))
        return minimum, recommended
