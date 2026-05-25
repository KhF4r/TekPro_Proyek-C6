"""
scrapers/pipeline.py
====================
Pipeline: orkestrasi RAWG → Steam → CheapShark, filter DLC, simpan hasil.
"""

import json
import math
import re
from datetime import datetime

from config.settings import MAX_SCRAPE, RAWG_API_KEY, OUTPUT_DIR, LATEST_JSON, log
from models.game import GameData
from .rawg import RAWGScraper
from .steam import SteamScraper
from .cheapshark import CheapSharkScraper

_DLC_PATTERNS = re.compile(
    r"\b("
    r"dlc|expansion|season pass|soundtrack|artbook|"
    r"blood and wine|hearts of stone|octo expansion|"
    r"ringed city|ashes of ariandel|old hunters|frozen wilds|"
    r"legacy of the void|heart of the swarm|wings of liberty complete|"
    r"complete edition|legendary edition|definitive edition|"
    r"game of the year edition|goty edition|"
    r"remastered|hd remaster|anniversary edition|ultimate edition|"
    r"bonus content|extra content|supporter pack|deluxe content"
    r")\b",
    re.IGNORECASE,
)


def _is_dlc(raw: dict) -> bool:
    if raw.get("parent_game") or raw.get("is_addon"):
        return True
    name = (raw.get("name") or "").lower()
    return bool(_DLC_PATTERNS.search(name))


class Pipeline:
    def __init__(self):
        self.rawg  = RAWGScraper(RAWG_API_KEY)
        self.steam = SteamScraper()
        self.cs    = CheapSharkScraper()

    def run_top(self, count=25, cb=None):
        count = min(count, MAX_SCRAPE)
        raw   = []
        for page in range(1, math.ceil(count / 25) + 1):
            raw.extend(self.rawg.top(page=page, size=25))
            if len(raw) >= count:
                break
        return self._process(raw[:count], cb)

    def run_search(self, query, count=25, cb=None):
        raw = self.rawg.search(query, size=min(count, 25))
        return self._process(raw[:count], cb)

    def _process(self, raw_list, cb=None):
        games   = []
        skipped = 0
        total   = len(raw_list)
        for i, raw in enumerate(raw_list, 1):
            if cb:
                cb(i, total, raw.get("name", ""))
            if _is_dlc(raw):
                log.info(f"Skipped DLC: {raw.get('name','?')}")
                skipped += 1
                continue
            try:
                g = self.rawg.parse(raw)
                g = self.steam.enrich(g)
                g = self.cs.enrich(g)
                games.append(g)
            except Exception as ex:
                log.error(f"Failed {raw.get('name','?')}: {ex}")
        if skipped:
            log.info(f"Filtered out {skipped} DLC/expansion entries")
        self._save(games)
        return games

    def _save(self, games):
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"bitscore_{ts}.json"
        data = [g.to_dict() for g in games]
        for p in [path, LATEST_JSON]:
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"Saved: {path}")
