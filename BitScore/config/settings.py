"""
config/settings.py
==================
Semua konstanta konfigurasi aplikasi: API keys, path, ukuran, dll.
"""

import os
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── API & Output ──────────────────────────────────────────────────────────────
RAWG_API_KEY  = os.getenv("RAWG_API_KEY", "31f10a65cb9947d9a6184288e7e2ce24")
OUTPUT_DIR    = Path(__file__).parent.parent / "output"
LATEST_JSON   = OUTPUT_DIR / "latest.json"
WISHLIST_JSON = OUTPUT_DIR / "wishlist.json"
REVIEWS_JSON  = OUTPUT_DIR / "reviews.json"
IMG_CACHE_DIR = OUTPUT_DIR / "img_cache"

OUTPUT_DIR.mkdir(exist_ok=True)
IMG_CACHE_DIR.mkdir(exist_ok=True)

# ── Pagination & Scraping ─────────────────────────────────────────────────────
PAGE_SIZE  = 25
MAX_SCRAPE = 200

# ── Genre & Tag Filters ───────────────────────────────────────────────────────
ALLOWED_GENRES = {"Action", "Horror", "Adventure", "Simulation", "RPG", "Racing",
                  "Arcade", "Sports"}

NOISY_TAGS = {
    "singleplayer", "multiplayer", "co-op", "online co-op", "local co-op",
    "split screen", "steam achievements", "steam cloud", "steam trading cards",
    "full controller support", "partial controller support", "controller",
    "steam workshop", "steam leaderboards", "vr support", "vr", "360 video",
    "cross-platform multiplayer", "mmo", "massively multiplayer",
    "early access", "free to play", "in-app purchases",
    "great soundtrack", "captions available", "commentary available",
    "remote play on tablet", "remote play on tv", "remote play on phone",
    "family sharing", "includes level editor",
}

# ── UI Layout ─────────────────────────────────────────────────────────────────
COVER_W, COVER_H = 184, 104   # landscape 16:9
SHOT_W,  SHOT_H  = 278, 156
NAV_TABS = ["All Games", "Wishlist", "Reviews", "Spec Recommender"]

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(OUTPUT_DIR / "bitscore.log")),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("BitScore")
