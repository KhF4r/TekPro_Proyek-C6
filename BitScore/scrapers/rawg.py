"""
scrapers/rawg.py
================
RAWGScraper: ambil data game dari RAWG.io API.
"""

from models.game import GameData
from config.settings import RAWG_API_KEY, NOISY_TAGS
from utils.helpers import strip_html
from .base import BaseScraper


class RAWGScraper(BaseScraper):
    BASE = "https://api.rawg.io/api"

    def __init__(self, key=RAWG_API_KEY):
        super().__init__(delay=0.3)
        self.key = key

    def _p(self, extra=None):
        p = {"key": self.key}
        p.update(extra or {})
        return p

    def top(self, page=1, size=25):
        d = self.get(f"{self.BASE}/games", self._p({
            "page": page, "page_size": size,
            "ordering": "-metacritic", "metacritic": "60,100",
            "dates": "2015-01-01,2026-12-31",
        }))
        return d.get("results", []) if d else []

    def search(self, q, size=25):
        d = self.get(f"{self.BASE}/games", self._p({
            "search": q, "page_size": size,
            "ordering": "-metacritic", "dates": "2015-01-01,2026-12-31",
        }))
        return d.get("results", []) if d else []

    def detail(self, slug):
        return self.get(f"{self.BASE}/games/{slug}", self._p())

    def shots(self, slug):
        d = self.get(f"{self.BASE}/games/{slug}/screenshots", self._p())
        return [s["image"] for s in (d or {}).get("results", [])]

    def parse(self, raw) -> GameData:
        slug = raw.get("slug", "")
        det  = self.detail(slug) or raw
        esrb = (det.get("esrb_rating") or {})
        return GameData(
            title=det.get("name", ""),
            slug=slug,
            description=strip_html(det.get("description", "")),
            release_date=det.get("released", ""),
            genres=[g["name"] for g in det.get("genres", [])],
            platforms=[p["platform"]["name"] for p in det.get("platforms", [])],
            developers=[d["name"] for d in det.get("developers", [])],
            publishers=[p["name"] for p in det.get("publishers", [])],
            tags=[t["name"] for t in det.get("tags", [])
                  if t["name"].lower() not in NOISY_TAGS][:12],
            cover_image=det.get("background_image", ""),
            screenshots=self.shots(slug)[:6],
            metacritic_score=det.get("metacritic"),
            rawg_rating=det.get("rating"),
            rawg_rating_count=det.get("ratings_count", 0),
            website=det.get("website", ""),
            age_rating=esrb.get("name", ""),
            source_rawg=True,
        )
