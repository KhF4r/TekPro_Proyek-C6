"""
processor/loader.py
-------------------
Fungsi untuk memuat data dari file JSON dan mengonversi GameData ke format UI.
"""

import json
import logging
from pathlib import Path

from .mapper import map_game

log = logging.getLogger("BitScore")


def load_json_file(path: Path) -> list:
    """Baca file JSON hasil scraping dan kembalikan list dict siap UI."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [map_game(item, i) for i, item in enumerate(raw)]


def gamedata_to_ui(games: list) -> list:
    """Konversi list GameData object → list dict siap UI."""
    return [map_game(g.to_dict(), i) for i, g in enumerate(games)]
