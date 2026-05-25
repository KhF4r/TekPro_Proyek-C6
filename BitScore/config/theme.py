"""
config/theme.py
===============
Design tokens: warna, font, dan helper UI.
"""

import tkinter.font as tkfont
import tkinter as tk

# ── Background Colors ─────────────────────────────────────────────────────────
BG_DEEP      = "#09080f"
BG_PANEL     = "#110f1c"
BG_CARD      = "#151220"
BG_CARD_HVR  = "#1c1830"
BG_SURFACE2  = "#1c1830"
BG_SURFACE3  = "#221e34"

# ── Accent ────────────────────────────────────────────────────────────────────
ACCENT       = "#7c6af7"
ACCENT_LIGHT = "#a594fa"
ACCENT_BG    = "#13102a"
ACCENT_DIM   = "#3d3580"

# ── Status Colors ─────────────────────────────────────────────────────────────
GREEN        = "#3ecf8e"
GREEN_BG     = "#091e14"
GREEN_DIM    = "#1a5c3a"
AMBER        = "#f5a62a"
AMBER_BG     = "#1c1206"
RED_COL      = "#e85d4a"
RED_BG       = "#1e0a08"
TEAL         = "#2dd4bf"
TEAL_BG      = "#071e1c"

# ── Text ──────────────────────────────────────────────────────────────────────
TEXT_WHITE   = "#edeaff"
TEXT_DIM     = "#6e6a88"
TEXT_MUTED   = "#3d3a52"

# ── Borders ───────────────────────────────────────────────────────────────────
BORDER       = "#1a1728"
BORDER2      = "#252140"

# ── Badge Colors ──────────────────────────────────────────────────────────────
GOLD_BADGE   = "#d4a830"
SILVER_BADGE = "#7a8ea8"
BRONZE_BADGE = "#a87060"
FREE_GREEN   = "#3ecf8e"
WARN_ORANGE  = "#f07830"


# ── Font Helpers ──────────────────────────────────────────────────────────────
def F(size, bold=False):
    """Font Segoe UI."""
    return tkfont.Font(family="Segoe UI", size=size, weight="bold" if bold else "normal")


def FM(size, bold=False):
    """Font Consolas (monospace)."""
    return tkfont.Font(family="Consolas", size=size, weight="bold" if bold else "normal")


# ── UI Helpers ────────────────────────────────────────────────────────────────
def divider(parent, color=BORDER2, height=1, padx=0, pady=8):
    """Horizontal divider line."""
    tk.Frame(parent, bg=color, height=height).pack(fill="x", padx=padx, pady=pady)


def genre_bg(genres):
    """Return background color based on game genre."""
    m = {
        "RPG": "#160e28", "Action": "#180a0a", "Adventure": "#081424",
        "Horror": "#120606", "Simulation": "#081808", "Racing": "#181006",
        "Sports": "#081428", "Arcade": "#180826", "Casual": "#081812",
    }
    for g in genres:
        if g in m:
            return m[g]
    return "#110c22"


def review_color(r):
    """Return color based on Steam review text."""
    r = r.lower()
    if "overwhelmingly positive" in r or "very positive" in r:
        return GREEN
    if "positive" in r:
        return GREEN
    if "mixed" in r:
        return AMBER
    if "negative" in r:
        return RED_COL
    return TEXT_DIM


def meta_color(s):
    """Return color based on Metacritic score."""
    if s is None:
        return TEXT_DIM
    return GREEN if s >= 85 else (AMBER if s >= 70 else RED_COL)
