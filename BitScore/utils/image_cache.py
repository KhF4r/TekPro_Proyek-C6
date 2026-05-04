"""
utils/image_cache.py
--------------------
Async image cache berbasis thread — fetch & cache cover/screenshot dari URL.
"""

import threading
from io import BytesIO
from urllib.request import urlopen, Request

from config.theme import COVER_W, COVER_H
from config.settings import PIL_AVAILABLE

if PIL_AVAILABLE:
    from PIL import Image, ImageTk, ImageOps


class ImageCache:
    """Thread-safe LRU-style cache untuk PhotoImage dari URL."""

    def __init__(self):
        self._cache: dict = {}
        self._lock        = threading.Lock()
        self._pending: dict = {}   # key → list of callbacks

    def get(self, url: str, size: tuple = (COVER_W, COVER_H),
            callback=None):
        """
        Ambil image dari cache. Jika belum ada, fetch di background thread.
        callback(img) dipanggil setelah fetch selesai (img bisa None jika gagal).
        """
        if not url:
            return None

        key = f"{url}|{size}"

        with self._lock:
            if key in self._cache:
                img = self._cache[key]
                if callback and img is not None:
                    callback(img)
                return img

            self._pending.setdefault(key, [])
            if callback:
                self._pending[key].append(callback)

            # Hanya start thread sekali per key
            if len(self._pending[key]) == (1 if callback else 0):
                threading.Thread(
                    target=self._fetch, args=(url, size, key), daemon=True
                ).start()

        return None

    def _fetch(self, url: str, size: tuple, key: str):
        img = None
        if PIL_AVAILABLE and url:
            try:
                req  = Request(url, headers={"User-Agent": "BitScore/1.0"})
                data = urlopen(req, timeout=8).read()
                pil  = Image.open(BytesIO(data)).convert("RGB")
                pil  = ImageOps.fit(pil, size, Image.LANCZOS)
                img  = ImageTk.PhotoImage(pil)
            except Exception:
                pass

        with self._lock:
            self._cache[key] = img
            callbacks = self._pending.pop(key, [])

        for cb in callbacks:
            if cb:
                cb(img)


# Singleton global untuk dipakai seluruh aplikasi
IMAGE_CACHE = ImageCache()
