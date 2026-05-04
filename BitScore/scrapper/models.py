"""
scraper/models.py
-----------------
Dataclass GameData sebagai model utama hasil scraping.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class GameData:
    title: str
    slug: str
    description: str          = ""
    release_date: str         = ""
    genres: list              = field(default_factory=list)
    platforms: list           = field(default_factory=list)
    developers: list          = field(default_factory=list)
    publishers: list          = field(default_factory=list)
    tags: list                = field(default_factory=list)
    cover_image: str          = ""
    screenshots: list         = field(default_factory=list)
    metacritic_score: Optional[int]   = None
    rawg_rating: Optional[float]      = None
    rawg_rating_count: int    = 0
    steam_appid: Optional[int]        = None
    steam_price_idr: Optional[str]    = None
    steam_price_usd: Optional[str]    = None
    steam_is_free: bool       = False
    steam_review_summary: str = ""
    deal_price: Optional[str] = None
    deal_store: Optional[str] = None
    deal_savings: Optional[str]       = None
    website: str              = ""
    age_rating: str           = ""
    pc_minimum: str           = ""
    pc_recommended: str       = ""
    source_rawg: bool         = False
    source_steam: bool        = False
    scraped_at: str           = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict:
        return asdict(self)
