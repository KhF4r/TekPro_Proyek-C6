"""
store/local_store.py
====================
LocalStore: penyimpanan lokal untuk Wishlist dan Review.

Review structure per slug:
  { slug: [ {username, score, text, date}, ... ] }
"""

import json
from datetime import datetime
from config.settings import WISHLIST_JSON, REVIEWS_JSON


class LocalStore:
    def __init__(self):
        self._wl: set  = set()
        self._rv: dict = {}   # { slug: [ {username, score, text, date} ] }
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self):
        if WISHLIST_JSON.exists():
            try:
                self._wl = set(json.loads(WISHLIST_JSON.read_text(encoding="utf-8")))
            except Exception:
                pass
        if REVIEWS_JSON.exists():
            try:
                raw = json.loads(REVIEWS_JSON.read_text(encoding="utf-8"))
                # Migrate format lama (single dict per slug) ke format baru (list per slug)
                migrated = {}
                for slug, val in raw.items():
                    if isinstance(val, list):
                        migrated[slug] = val
                    elif isinstance(val, dict):
                        migrated[slug] = [{
                            "username": val.get("username", "user"),
                            "score":    val.get("score", 0),
                            "text":     val.get("text", ""),
                            "date":     val.get("date", ""),
                        }]
                self._rv = migrated
            except Exception:
                pass

    def _save_wl(self):
        WISHLIST_JSON.write_text(
            json.dumps(list(self._wl), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_rv(self):
        REVIEWS_JSON.write_text(
            json.dumps(self._rv, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── Wishlist ──────────────────────────────────────────────────────────────
    def in_wl(self, slug: str) -> bool:
        return slug in self._wl

    def toggle_wl(self, slug: str) -> bool:
        if self.in_wl(slug):
            self._wl.discard(slug)
        else:
            self._wl.add(slug)
        self._save_wl()
        return self.in_wl(slug)

    @property
    def wishlist(self) -> set:
        return self._wl

    # ── Reviews ───────────────────────────────────────────────────────────────
    def get_reviews(self, slug: str) -> list:
        """Return list of review dicts for this game."""
        return self._rv.get(slug, [])

    def get_user_review(self, slug: str, username: str) -> dict:
        """Return review dict for a specific user, or empty dict."""
        for rv in self._rv.get(slug, []):
            if rv.get("username", "").lower() == username.lower():
                return rv
        return {}

    def has_user_review(self, slug: str, username: str) -> bool:
        return bool(self.get_user_review(slug, username))

    def set_rv(self, slug: str, score: int, text: str, username: str = "user"):
        """Simpan atau update review milik username untuk game slug."""
        reviews = self._rv.get(slug, [])
        for rv in reviews:
            if rv.get("username", "").lower() == username.lower():
                rv["score"] = score
                rv["text"]  = text
                rv["date"]  = datetime.now().strftime("%d/%m/%Y %H:%M")
                self._rv[slug] = reviews
                self._save_rv()
                return
        reviews.append({
            "username": username,
            "score":    score,
            "text":     text,
            "date":     datetime.now().strftime("%d/%m/%Y %H:%M"),
        })
        self._rv[slug] = reviews
        self._save_rv()

    def del_rv(self, slug: str, username: str = None):
        """
        Hapus review:
          - Jika username diberikan: hapus review milik user tsb saja
          - Jika username None: hapus semua review untuk slug (admin)
        """
        if username is None:
            self._rv.pop(slug, None)
        else:
            reviews = self._rv.get(slug, [])
            reviews = [r for r in reviews if r.get("username", "").lower() != username.lower()]
            if reviews:
                self._rv[slug] = reviews
            else:
                self._rv.pop(slug, None)
        self._save_rv()

    def has_rv(self, slug: str) -> bool:
        return bool(self._rv.get(slug))

    # Backward compat
    def get_rv(self, slug: str) -> dict:
        reviews = self._rv.get(slug, [])
        return reviews[0] if reviews else {"score": 0, "text": "", "date": ""}

    @property
    def reviews(self) -> dict:
        return self._rv


# Singleton
STORE = LocalStore()
