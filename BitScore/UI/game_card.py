"""
ui/game_card.py
---------------
Builder untuk satu card game di daftar utama (main list).
"""

import math
import tkinter as tk
import tkinter.font as tkfont

from config.theme import (
    BG_CARD, BG_CARD_HVR, COVER_W, COVER_H,
    ACCENT_GOLD, ACCENT_PURP,
    GOLD_BADGE, SILVER_BADGE, BRONZE_BADGE,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    GENRE_BG, GENRE_TXT, FREE_GREEN, WARN_ORANGE,
)
from processor.mapper import meta_color, review_color
from utils.image_cache import IMAGE_CACHE


def _recolor(widget, color: str):
    """Rekursif ganti warna bg widget dan semua child-nya (kecuali Canvas)."""
    try:
        if widget.winfo_class() != "Canvas":
            widget.configure(bg=color)
    except Exception:
        pass
    for child in widget.winfo_children():
        _recolor(child, color)


def build_game_card(parent, game: dict, rank: int, fonts: dict,
                    on_click, after_fn) -> tk.Frame:
    """
    Buat dan return frame card game.

    Parameters
    ----------
    parent   : container frame
    game     : UI dict (dari processor/mapper)
    rank     : posisi tampil (1-based, menentukan warna badge)
    fonts    : dict font dari ui/fonts.py
    on_click : callable(game) dipanggil saat card diklik
    after_fn : tk root.after — dipakai untuk schedule image load
    """
    card = tk.Frame(parent, bg=BG_CARD, cursor="hand2")
    card.pack(fill="x", pady=4, padx=2)

    hover_on  = lambda e: _recolor(card, BG_CARD_HVR)
    hover_off = lambda e: _recolor(card, BG_CARD)

    card.bind("<Enter>",    hover_on)
    card.bind("<Leave>",    hover_off)
    card.bind("<Button-1>", lambda e, g=game: on_click(g))

    _add_rank_badge(card, rank, fonts)
    _add_cover(card, game, after_fn, hover_on, hover_off, on_click)
    _add_info(card, game, fonts, hover_on, hover_off, on_click)
    _add_right_col(card, game, fonts, hover_on, hover_off, on_click)

    return card


# ── Private helpers ────────────────────────────────────────────────────────────

def _add_rank_badge(card, rank: int, fonts: dict):
    bc = {1: GOLD_BADGE, 2: SILVER_BADGE, 3: BRONZE_BADGE}.get(rank, ACCENT_PURP)
    bv = tk.Canvas(card, width=46, height=70, bg=BG_CARD, highlightthickness=0)
    bv.pack(side="left", padx=(8, 0), pady=8)

    pts = []
    for i in range(6):
        a = math.radians(60 * i - 90)
        pts.extend([23 + 19 * math.cos(a), 35 + 19 * math.sin(a)])
    bv.create_polygon(pts, fill=bc, outline="", smooth=False)
    bv.create_text(23, 35, text=str(rank), font=fonts["badge"], fill=TEXT_WHITE)
    return bv


def _add_cover(card, game: dict, after_fn, hover_on, hover_off, on_click):
    cv = tk.Canvas(card, width=COVER_W, height=COVER_H,
                   bg=game["color"], highlightthickness=0)
    cv.pack(side="left", padx=8, pady=8)
    cv.create_text(
        COVER_W // 2, COVER_H // 2, text=game["title"][0],
        font=tkfont.Font(family="Georgia", size=26, weight="bold"),
        fill="white",
    )

    def _sc(img, c=cv):
        if img:
            c._img = img
            c.create_image(0, 0, anchor="nw", image=img)

    IMAGE_CACHE.get(game["cover_url"], size=(COVER_W, COVER_H),
                    callback=lambda img, fn=_sc: after_fn(0, fn, img))
    cv.bind("<Enter>",    hover_on)
    cv.bind("<Leave>",    hover_off)
    cv.bind("<Button-1>", lambda e, g=game: on_click(g))


def _add_info(card, game: dict, fonts: dict, hover_on, hover_off, on_click):
    inf = tk.Frame(card, bg=BG_CARD)
    inf.pack(side="left", fill="both", expand=True, pady=10)

    tk.Label(inf, text=game["title"], font=fonts["title"],
             fg=TEXT_WHITE, bg=BG_CARD, anchor="w").pack(fill="x")

    # Genre tags
    gr = tk.Frame(inf, bg=BG_CARD)
    gr.pack(fill="x", pady=(3, 0))
    for genre in game["genres"]:
        tk.Label(gr, text=genre, font=fonts["genre"],
                 fg=GENRE_TXT, bg=GENRE_BG,
                 padx=6, pady=2).pack(side="left", padx=(0, 3))

    # Platforms
    if game["platforms"]:
        plat = ", ".join(game["platforms"][:3])
        if len(game["platforms"]) > 3:
            plat += f"  +{len(game['platforms'])-3}"
        tk.Label(inf, text=plat, font=fonts["small"],
                 fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(2, 0))

    # Rating row
    rr = tk.Frame(inf, bg=BG_CARD)
    rr.pack(fill="x", pady=(6, 0))

    rb = tk.Frame(rr, bg=ACCENT_GOLD)
    rb.pack(side="left", padx=(0, 6))
    tk.Label(rb, text=f"★ {game['rating']:.2f}",
             font=fonts["rating"], fg=TEXT_WHITE,
             bg=ACCENT_GOLD, padx=7, pady=3).pack()

    mc = game.get("metacritic")
    if mc:
        mb = tk.Frame(rr, bg=meta_color(mc))
        mb.pack(side="left", padx=(0, 6))
        tk.Label(mb, text=f"MC {mc}", font=fonts["meta"],
                 fg=TEXT_WHITE, bg=meta_color(mc), padx=6, pady=3).pack()

    pr_c = FREE_GREEN if game["is_free"] else (
        WARN_ORANGE if game.get("deal_price") else
        (ACCENT_PURP if game["price"] != "N/A" else TEXT_MUTED))
    price_txt = game["price"]
    if game.get("deal_savings"):
        price_txt += f"  💸 -{game['deal_savings']}"
    tk.Label(rr, text=price_txt, font=fonts["price"],
             fg=pr_c, bg=BG_CARD, padx=4).pack(side="left")

    for w in [inf, gr, rr, rb]:
        w.bind("<Enter>",    hover_on)
        w.bind("<Leave>",    hover_off)
        w.bind("<Button-1>", lambda e, g=game: on_click(g))


def _add_right_col(card, game: dict, fonts: dict, hover_on, hover_off, on_click):
    rc = tk.Frame(card, bg=BG_CARD)
    rc.pack(side="right", padx=12, pady=10, anchor="ne")

    tk.Label(rc, text=game["developer"], font=fonts["dev"],
             fg=TEXT_MUTED, bg=BG_CARD, anchor="e").pack(anchor="e")

    if game.get("age_rating"):
        tk.Label(rc, text=f"🔞 {game['age_rating']}", font=fonts["small"],
                 fg=TEXT_DIM, bg=BG_CARD).pack(anchor="e", pady=(2, 0))

    if game["review"]:
        tk.Label(rc, text=game["review"][:26], font=fonts["small"],
                 fg=review_color(game["review"]),
                 bg=BG_CARD, anchor="e").pack(anchor="e", pady=(4, 0))

    if game["rawg_count"]:
        tk.Label(rc, text=f"({game['rawg_count']:,} ratings)",
                 font=fonts["small"], fg=TEXT_MUTED,
                 bg=BG_CARD).pack(anchor="e", pady=(2, 0))

    rc.bind("<Enter>",    hover_on)
    rc.bind("<Leave>",    hover_off)
    rc.bind("<Button-1>", lambda e, g=game: on_click(g))
