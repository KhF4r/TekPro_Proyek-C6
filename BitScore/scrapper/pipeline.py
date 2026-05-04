"""
scraper/pipeline.py
-------------------
BitScorePipeline — orkestrasi scraping dari RAWG, Steam, dan CheapShark,
lalu menyimpan hasilnya ke disk.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .rawg import RAWGScraper
from .steam import SteamScraper
from .cheapshark import CheapSharkScraper
from .models import GameData

log = logging.getLogger("BitScore")

ProgressCallback = Optional[Callable[[int, int, str], None]]


class BitScorePipeline:
    def __init__(self, rawg_key: str, output_dir: str = "output"):
        self.rawg       = RAWGScraper(api_key=rawg_key)
        self.steam      = SteamScraper()
        self.cheapshark = CheapSharkScraper()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    # ── Public entry points ───────────────────────────────────────────────────

    def scrape_top_games(self, count: int = 20,
                         progress_cb: ProgressCallback = None) -> list[GameData]:
        raw_list = self.rawg.get_top_games(page_size=count)
        return self._process_list(raw_list, progress_cb)

    def scrape_by_query(self, query: str, limit: int = 10,
                        progress_cb: ProgressCallback = None) -> list[GameData]:
        raw_list = self.rawg.search_games(query, page_size=limit)
        return self._process_list(raw_list, progress_cb)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _process_list(self, raw_list: list,
                      progress_cb: ProgressCallback = None) -> list[GameData]:
        games = []
        total = len(raw_list)
        for i, raw in enumerate(raw_list, 1):
            if progress_cb:
                progress_cb(i, total, raw.get("name", ""))
            game = self._process_one(raw)
            if game:
                games.append(game)
        self._save(games)
        return games

    def _process_one(self, raw: dict) -> Optional[GameData]:
        try:
            game = self.rawg.parse_game(raw)
            game = self.steam.enrich_game(game)
            game = self.cheapshark.enrich_game(game)
            return game
        except Exception as e:
            log.error(f"Gagal memproses '{raw.get('name', '?')}': {e}")
            return None

    def _save(self, games: list[GameData]) -> Path:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"bitscore_{ts}.json"
        data = [g.to_dict() for g in games]

        for dest in [path, self.output_dir / "latest.json"]:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        log.info(f"✅ Tersimpan: {path}")
        return path
