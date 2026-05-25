"""
scrapers/base.py
================
BaseScraper: HTTP session dengan retry dan delay.
"""

import time
import requests
from config.settings import log


class BaseScraper:
    def __init__(self, delay=0.5, retries=3):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "BitScore/4.0"
        self.delay   = delay
        self.retries = retries

    def get(self, url, params=None):
        for attempt in range(1, self.retries + 1):
            try:
                time.sleep(self.delay)
                r = self.session.get(url, params=params, timeout=10)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                log.error(f"GET fail ({attempt}): {e}")
                if attempt == self.retries:
                    return None
                time.sleep(2 ** attempt)
        return None
