"""
scrapers/cheapshark.py
======================
CheapSharkScraper: enrich GameData dengan info diskon dari CheapShark API.
"""

from .base import BaseScraper

_PC_PLATFORMS = {"PC", "Windows", "macOS", "Linux", "Mac"}


class CheapSharkScraper(BaseScraper):
    BASE = "https://www.cheapshark.com/api/1.0"

    def __init__(self):
        super().__init__(delay=0.5)

    def _is_pc_game(self, g) -> bool:
        return bool(set(g.platforms) & _PC_PLATFORMS)

    def enrich(self, g):
        if not self._is_pc_game(g):
            return g

        items = self.get(f"{self.BASE}/games", {"title": g.title, "limit": 3})
        if not items:
            return g

        for item in items:
            did = item.get("cheapestDealID")
            if did:
                deal = self.get(f"{self.BASE}/deals", {"id": did})
                if deal:
                    info     = deal.get("gameInfo", {})
                    sale     = info.get("salePrice", "")
                    retail   = info.get("retailPrice", "")
                    savings  = float(info.get("savings", 0))
                    if savings >= 5:
                        g.deal_price   = f"${sale}"
                        g.deal_savings = f"{savings:.0f}%"
                    if not g.steam_price_usd and not g.steam_is_free:
                        price_to_use = sale if sale and sale != "0.00" else retail
                        if price_to_use and price_to_use != "0.00":
                            g.steam_price_usd = f"${price_to_use}"
                break

        return g
