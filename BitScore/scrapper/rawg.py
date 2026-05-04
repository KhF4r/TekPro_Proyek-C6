"""
scraper/rawg.py
---------------
Scraper untuk RAWG API — search, detail, screenshots, top games.
"""

import re
import logging
from .base import BaseScraper
from .models import GameData

log = logging.getLogger("BitScore")


def _strip_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", clean).strip()


class RAWGScraper(BaseScraper):
    BASE_URL = "https://api.rawg.io/api"

    def __init__(self, api_key: str):
        super().__init__(delay=0.3)
        self.api_key = api_key

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _params(self, extra: dict = None) -> dict:
        p = {"key": self.api_key}
        if extra:
            p.update(extra)
        return p

    # ── Public API ────────────────────────────────────────────────────────────

    def search_games(self, query: str, page_size: int = 10) -> list:
        data = self.get(
            f"{self.BASE_URL}/games",
            params=self._params({"search": query, "page_size": page_size,
                                 "ordering": "-rating"}),
        )
        return data.get("results", []) if data else []

    def get_game_detail(self, slug: str) -> dict:
        return self.get(f"{self.BASE_URL}/games/{slug}", params=self._params())

    def get_game_screenshots(self, slug: str) -> list:
        data = self.get(
            f"{self.BASE_URL}/games/{slug}/screenshots",
            params=self._params(),
        )
        return [s["image"] for s in data.get("results", [])] if data else []

    def get_top_games(self, page: int = 1, page_size: int = 20,
                      ordering: str = "-rating") -> list:
        data = self.get(
            f"{self.BASE_URL}/games",
            params=self._params({"page": page, "page_size": page_size,
                                 "ordering": ordering, "metacritic": "60,100"}),
        )
        return data.get("results", []) if data else []

    def parse_game(self, raw: dict, fetch_screenshots: bool = True) -> GameData:
        slug   = raw.get("slug", "")
        detail = self.get_game_detail(slug) or raw
        shots  = self.get_game_screenshots(slug)[:6] if fetch_screenshots else []

        esrb       = detail.get("esrb_rating") or {}
        age_rating = esrb.get("name", "")

        return GameData(
            title            = detail.get("name", ""),
            slug             = slug,
            description      = _strip_html(detail.get("description", "")),
            release_date     = detail.get("released", ""),
            genres           = [g["name"] for g in detail.get("genres", [])],
            platforms        = [p["platform"]["name"] for p in detail.get("platforms", [])],
            developers       = [d["name"] for d in detail.get("developers", [])],
            publishers       = [p["name"] for p in detail.get("publishers", [])],
            tags             = [t["name"] for t in detail.get("tags", [])[:15]],
            cover_image      = detail.get("background_image", ""),
            screenshots      = shots,
            metacritic_score = detail.get("metacritic"),
            rawg_rating      = detail.get("rating"),
            rawg_rating_count= detail.get("ratings_count", 0),
            website          = detail.get("website", ""),
            age_rating       = age_rating,
            source_rawg      = True,
        )
