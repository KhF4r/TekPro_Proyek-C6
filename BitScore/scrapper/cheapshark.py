"""
scraper/cheapshark.py
---------------------
Scraper untuk CheapShark API — mengambil data deal/diskon game.
"""

import logging
from .base import BaseScraper
from .models import GameData

log = logging.getLogger("BitScore")


class CheapSharkScraper(BaseScraper):
    BASE_URL = "https://www.cheapshark.com/api/1.0"

    def __init__(self):
        super().__init__(delay=0.5)

    def enrich_game(self, game: GameData) -> GameData:
        data = self.get(
            f"{self.BASE_URL}/games",
            params={"title": game.title, "limit": 3, "exact": 0},
        )
        if not data:
            return game

        for g in data:
            deal_id = g.get("cheapestDealID")
            if deal_id:
                deal = self.get(f"{self.BASE_URL}/deals", params={"id": deal_id})
                if deal:
                    info              = deal.get("gameInfo", {})
                    game.deal_price   = f"${info.get('salePrice', '')}"
                    game.deal_savings = f"{float(info.get('savings', 0)):.0f}%"
                break

        return game
