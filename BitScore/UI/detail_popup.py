"""
ui/detail_popup.py
------------------
DetailPopup — jendela detail game dengan 3 tab:
  Info & Deskripsi | Preview Screenshots | PC Requirements
"""

import tkinter as tk
import tkinter.font as tkfont

from config.theme import (
    BG_DEEP, BG_PANEL, BG_TAB, BG_TAB_ACT, BORDER_COL,
    ACCENT_GOLD, ACCENT_PURP, ACCENT_LIGHT,
    TEXT_WHITE, TEXT_DIM, FREE_GREEN, WARN_ORANGE,
    GENRE_BG, GENRE_TXT,
)
from processor.mapper import meta_color, review_color
from utils.image_cache import IMAGE_CACHE
from ui.detail_tabs import build_info_tab, build_preview_tab, build_requirements_tab
from ui.fonts import build_fonts


class DetailPopup(tk.Toplevel):
    def __init__(self, parent, game: dict):
        super().__init__(parent)
        self.game        = game
        self._shot_images = []   # prevent GC on screenshot PhotoImages
        self.fonts       = build_fonts()

        self.title(game["title"])
        self.configure(bg=BG_DEEP)
        self.geometry("860x640")
        self.minsize(800, 580)
        self.resizable(True, True)
        self.grab_set()

        self._build_header()
        self._build_tabs()

        tk.Button(
            self, text="✕  Tutup", font=self.fonts["sub"],
            fg=TEXT_WHITE, bg=ACCENT_PURP,
            activebackground=ACCENT_LIGHT, activeforeground=TEXT_WHITE,
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self.destroy,
        ).pack(pady=(6, 12))

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        top = tk.Frame(self, bg=BG_PANEL)
        top.pack(fill="x")

        # Cover canvas
        self.cv = tk.Canvas(top, width=160, height=160,
                            bg=self.game["color"], highlightthickness=0)
        self.cv.pack(side="left", padx=16, pady=16)
        self.cv.create_text(
            80, 80, text=self.game["title"][0],
            font=tkfont.Font(family="Georgia", size=48, weight="bold"),
            fill="white",
        )
        IMAGE_CACHE.get(self.game["cover_url"], size=(160, 160),
                        callback=lambda img: self.after(0, self._set_cover, img))

        # Info block
        inf = tk.Frame(top, bg=BG_PANEL)
        inf.pack(side="left", fill="both", expand=True, pady=16, padx=(0, 16))
        self._build_header_info(inf)

    def _set_cover(self, img):
        if img:
            self.cv._img = img
            self.cv.delete("all")
            self.cv.create_image(0, 0, anchor="nw", image=img)

    def _build_header_info(self, inf):
        g = self.game
        tk.Label(inf, text=g["title"], font=self.fonts["big"],
                 fg=TEXT_WHITE, bg=BG_PANEL,
                 wraplength=560, justify="left").pack(anchor="w")

        meta_txt = g["developer"]
        if g.get("publisher"):
            meta_txt += f"  |  {g['publisher']}"
        meta_txt += f"  ·  {g['year']}"
        tk.Label(inf, text=meta_txt, font=self.fonts["small"],
                 fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w", pady=(2, 6))

        # Age rating & release date
        age_row = tk.Frame(inf, bg=BG_PANEL)
        age_row.pack(anchor="w", pady=(0, 4))
        if g.get("age_rating"):
            box = tk.Frame(age_row, bg=BORDER_COL)
            box.pack(side="left", padx=(0, 8))
            tk.Label(box, text=f"🔞 {g['age_rating']}",
                     font=self.fonts["small"], fg=TEXT_WHITE,
                     bg=BORDER_COL, padx=8, pady=3).pack()
        if g.get("release_date"):
            tk.Label(age_row, text=f"📅 Rilis: {g['release_date']}",
                     font=self.fonts["small"], fg=TEXT_DIM,
                     bg=BG_PANEL).pack(side="left")

        # Genre tags
        gr = tk.Frame(inf, bg=BG_PANEL)
        gr.pack(anchor="w")
        for genre in g["genres"]:
            tk.Label(gr, text=genre, font=self.fonts["small"],
                     fg=GENRE_TXT, bg=GENRE_BG,
                     padx=6, pady=2).pack(side="left", padx=(0, 4))

        # Rating row
        rr = tk.Frame(inf, bg=BG_PANEL)
        rr.pack(anchor="w", pady=(8, 0))
        rb = tk.Frame(rr, bg=ACCENT_GOLD)
        rb.pack(side="left", padx=(0, 8))
        tk.Label(rb, text=f"★ {g['rating']:.2f}  RAWG",
                 font=self.fonts["badge"], fg=TEXT_WHITE,
                 bg=ACCENT_GOLD, padx=8, pady=4).pack()

        mc = g.get("metacritic")
        if mc:
            mb = tk.Frame(rr, bg=meta_color(mc))
            mb.pack(side="left", padx=(0, 8))
            tk.Label(mb, text=f"Metacritic {mc}",
                     font=self.fonts["badge"], fg=TEXT_WHITE,
                     bg=meta_color(mc), padx=8, pady=4).pack()

        pr_c = FREE_GREEN if g["is_free"] else ACCENT_PURP
        tk.Label(rr, text=g["price"], font=self.fonts["badge"],
                 fg=pr_c, bg=BG_PANEL, padx=4).pack(side="left")

        if g.get("deal_price") and g.get("deal_savings"):
            tk.Label(inf,
                     text=f"💸 Deal: {g['deal_price']}  (hemat {g['deal_savings']})",
                     font=self.fonts["small"], fg=WARN_ORANGE,
                     bg=BG_PANEL).pack(anchor="w", pady=(4, 0))
        if g["review"]:
            tk.Label(inf, text=f"Steam: {g['review']}",
                     font=self.fonts["small"],
                     fg=review_color(g["review"]),
                     bg=BG_PANEL).pack(anchor="w", pady=(4, 0))

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _build_tabs(self):
        tab_bar = tk.Frame(self, bg=BG_DEEP)
        tab_bar.pack(fill="x")
        tk.Frame(tab_bar, bg=BORDER_COL, height=2).pack(side="bottom", fill="x")

        self._tab_content = tk.Frame(self, bg=BG_DEEP)
        self._tab_content.pack(fill="both", expand=True)

        self._tab_btns   = {}
        self._tab_frames = {}

        tab_defs = [
            ("info",         "📋  Info & Deskripsi"),
            ("preview",      "🖼️  Preview"),
            ("requirements", "💻  PC Requirements"),
        ]
        for tab_id, label in tab_defs:
            btn = tk.Button(
                tab_bar, text=label, font=self.fonts["tab"],
                fg=TEXT_WHITE, bg=BG_TAB,
                activebackground=BG_TAB_ACT, activeforeground=TEXT_WHITE,
                relief="flat", cursor="hand2", padx=18, pady=8,
                command=lambda tid=tab_id: self._switch_tab(tid),
            )
            btn.pack(side="left")
            self._tab_btns[tab_id] = btn

        self._tab_frames["info"] = build_info_tab(
            self._tab_content, self.game, self.fonts)
        self._tab_frames["preview"] = build_preview_tab(
            self._tab_content, self.game, self.fonts,
            self.after, self._shot_images)
        self._tab_frames["requirements"] = build_requirements_tab(
            self._tab_content, self.game, self.fonts)

        self._switch_tab("info")

    def _switch_tab(self, tab_id: str):
        for tid, btn in self._tab_btns.items():
            btn.configure(bg=BG_TAB_ACT if tid == tab_id else BG_TAB)
        for tid, frame in self._tab_frames.items():
            if tid == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
