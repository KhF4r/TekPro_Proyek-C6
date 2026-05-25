"""
ui/pages/home_page.py
=====================
Halaman utama: daftar game dengan filter genre, platform, sort, dan pagination.
"""

import math
import tkinter as tk
import tkinter.ttk as ttk

from config.settings import PAGE_SIZE, MAX_SCRAPE, LATEST_JSON
from config.theme import (
    BG_DEEP, BG_PANEL, BG_SURFACE3, BG_SURFACE2,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_DIM,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED, AMBER,
    F, divider,
)
from store.local_store import STORE
from models.mapper import load_json
from UI.components.game_card import build_card


class HomePage(tk.Frame):
    """
    Frame halaman utama. Memerlukan reference ke app (parent_app)
    untuk akses state global: games, sort, filter, dsb.
    """

    def __init__(self, master, parent_app):
        super().__init__(master, bg=BG_DEEP)
        self.app = parent_app
        self._build()

    # ── Build Layout ──────────────────────────────────────────────────────────
    def _build(self):
        body = tk.Frame(self, bg=BG_DEEP)
        body.pack(fill="both", expand=True)

        # Sidebar (kanan)
        sidebar = tk.Frame(body, bg=BG_PANEL, width=210)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(sidebar, bg=BORDER2, width=1).pack(side="left", fill="y")
        sb = tk.Frame(sidebar, bg=BG_PANEL)
        sb.pack(fill="both", expand=True, padx=14)

        # Platform filter
        tk.Label(sb, text="PLATFORM", font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(14, 5))
        plat_opts = [("All Platforms", ACCENT_LIGHT), ("PC", "#3ecf8e"), ("Other Platforms", TEXT_DIM)]
        self._plat_btns = {}
        for plabel, _ in plat_opts:
            btn = tk.Button(sb, text=plabel, font=F(9), fg=TEXT_DIM, bg=BG_SURFACE3,
                            relief="flat", cursor="hand2", padx=10, pady=6, anchor="w",
                            activebackground=BG_SURFACE2, activeforeground=TEXT_WHITE,
                            command=lambda p=plabel: self._set_platform(p))
            btn.pack(fill="x", pady=2)
            self._plat_btns[plabel] = btn
        self._plat_btns["All Platforms"].configure(fg=TEXT_WHITE, bg=ACCENT_DIM)
        self.app._active_platform.set("All Platforms")

        # Genre filter
        divider(sb, pady=0)
        tk.Label(sb, text="GENRE", font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(10, 6))
        self.genre_frame = tk.Frame(sb, bg=BG_PANEL)
        self.genre_frame.pack(fill="x")
        self.genre_btns: dict = {}

        # Wishlist count
        divider(sb, pady=(14, 0))
        self.wl_lbl = tk.Label(sb, text="", font=F(9), fg=AMBER, bg=BG_PANEL)
        self.wl_lbl.pack(anchor="w", pady=(8, 0))

        # Main area
        main = tk.Frame(body, bg=BG_DEEP)
        main.pack(side="left", fill="both", expand=True)

        # Toolbar
        tb = tk.Frame(main, bg=BG_PANEL, height=40)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tk.Frame(tb, bg=BORDER2, height=1).pack(side="bottom", fill="x")
        self.count_lbl = tk.Label(tb, text="", font=F(9), fg=TEXT_MUTED, bg=BG_PANEL)
        self.count_lbl.pack(side="left", padx=16, pady=8)
        self.status_lbl = tk.Label(tb, text="", font=F(9), fg=AMBER, bg=BG_PANEL)
        self.status_lbl.pack(side="left", padx=4)
        self.sort_btn = tk.Button(tb, text="Metacritic  ↓", font=F(9), fg=TEXT_DIM,
                                  bg=BG_PANEL, relief="flat", cursor="hand2",
                                  padx=10, pady=4, activebackground=BG_SURFACE2,
                                  activeforeground=TEXT_WHITE,
                                  command=self.app._open_sort_popup)
        self.sort_btn.pack(side="right", padx=8)

        # Scrollable list
        lc = tk.Frame(main, bg=BG_DEEP)
        lc.pack(fill="both", expand=True)
        self.cvlist = tk.Canvas(lc, bg=BG_DEEP, highlightthickness=0)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Vertical.TScrollbar",
                        troughcolor=BG_PANEL, background=BG_SURFACE3,
                        darkcolor=BORDER2, lightcolor=BORDER2,
                        arrowcolor=TEXT_MUTED, bordercolor=BG_PANEL,
                        relief="flat", arrowsize=10)
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", ACCENT_DIM), ("!active", BG_SURFACE3)])
        vsb = ttk.Scrollbar(lc, orient="vertical", command=self.cvlist.yview,
                            style="Dark.Vertical.TScrollbar")
        self.cvlist.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.cvlist.pack(side="left", fill="both", expand=True)
        self.gf = tk.Frame(self.cvlist, bg=BG_DEEP)
        self.cw = self.cvlist.create_window((0, 0), window=self.gf, anchor="nw")
        self.gf.bind("<Configure>", lambda e: self.cvlist.configure(scrollregion=self.cvlist.bbox("all")))
        self.cvlist.bind("<Configure>", lambda e: self.cvlist.itemconfig(self.cw, width=e.width))

        def _scroll(e):
            self.cvlist.yview_scroll(int(-1 * (e.delta / 120)), "units")

        self.cvlist.bind("<MouseWheel>", _scroll)
        self.gf.bind("<MouseWheel>", _scroll)
        self._scroll_fn = _scroll

        # Pagination bar
        self.pag_bar = tk.Frame(main, bg=BG_PANEL, height=46)
        self.pag_bar.pack(fill="x", side="bottom")
        self.pag_bar.pack_propagate(False)
        tk.Frame(self.pag_bar, bg=BORDER2, height=1).pack(fill="x", side="top")
        self._pag = tk.Frame(self.pag_bar, bg=BG_PANEL)
        self._pag.pack(expand=True)

    # ── Public: render daftar game ────────────────────────────────────────────
    def render(self):
        if not hasattr(self, "gf"):
            return
        for w in self.gf.winfo_children():
            w.destroy()
        for w in self._pag.winfo_children():
            w.destroy()
        self._update_wl_count()

        tab      = self.app._active_nav.get()
        filtered = self.app._filtered()
        total    = len(filtered)
        pages    = max(1, math.ceil(total / PAGE_SIZE))
        self.app._page = max(1, min(self.app._page, pages))
        start = (self.app._page - 1) * PAGE_SIZE
        pg    = filtered[start: start + PAGE_SIZE]

        self.count_lbl.configure(
            text=f"{total} games  ·  Page {self.app._page}/{pages}  ·  max scrape {MAX_SCRAPE}")

        if not pg:
            msgs = {
                "Wishlist":   "Wishlist is empty.\nOpen a game → click ♡ Add to Wishlist.",
                "Reviews": "No reviews yet.\nOpen a game → the ★ Reviews tab.",
            }
            tk.Label(self.gf, text=msgs.get(tab, "Tidak ada game."),
                     font=F(11), fg=TEXT_DIM, bg=BG_DEEP, justify="center").pack(pady=70)
            return

        show_rv = (tab == "Reviews")
        for rank, game in enumerate(pg, start + 1):
            original_rank = game.get("_rank", rank)
            build_card(self.gf, game, original_rank,
                       open_detail_cb=self.app._open_detail,
                       show_rank=True, show_rv=show_rv)

        # Reset scroll position and recalculate scrollregion after content is built
        self.cvlist.update_idletasks()
        self.cvlist.configure(scrollregion=self.cvlist.bbox("all"))
        self.cvlist.yview_moveto(0)

        # Pagination
        if pages > 1:
            def go(p):
                self.app._page = p
                self.render()
                self.cvlist.yview_moveto(0)

            def pb(txt, cmd, enabled=True, active=False):
                bg = ACCENT if active else (BG_SURFACE3 if enabled else BG_PANEL)
                fg = TEXT_WHITE if enabled else TEXT_MUTED
                tk.Button(self._pag, text=txt, font=F(9, active), fg=fg, bg=bg,
                          relief="flat", cursor="hand2" if enabled else "arrow",
                          padx=10, pady=5,
                          state="normal" if enabled else "disabled",
                          command=(lambda: cmd()) if enabled else None).pack(side="left", padx=2)

            pb("←", lambda: go(self.app._page - 1), self.app._page > 1)
            shown = set()
            cur = self.app._page
            for p in range(1, pages + 1):
                if p == 1 or p == pages or abs(p - cur) <= 2:
                    pb(str(p), lambda pg=p: go(pg), active=(p == cur))
                    shown.add(p)
                elif p - 1 in shown:
                    tk.Label(self._pag, text="...", font=F(9), fg=TEXT_MUTED, bg=BG_PANEL).pack(side="left", padx=2)
            pb("→", lambda: go(self.app._page + 1), self.app._page < pages)

    # ── Sidebar helpers ───────────────────────────────────────────────────────
    def refresh_genres(self, all_genres: list):
        for w in self.genre_frame.winfo_children():
            w.destroy()
        self.genre_btns.clear()
        for genre in all_genres:
            btn = tk.Button(self.genre_frame, text=genre, font=F(9), fg=TEXT_DIM, bg=BG_SURFACE3,
                            relief="flat", cursor="hand2", padx=8, pady=4, anchor="w",
                            command=lambda g=genre: self.app._toggle_genre(g))
            btn.pack(fill="x", pady=2)
            self.genre_btns[genre] = btn

    def _set_platform(self, plabel: str):
        self.app._active_platform.set(plabel)
        for p, btn in self._plat_btns.items():
            if p == plabel:
                btn.configure(fg=TEXT_WHITE, bg=ACCENT_DIM)
            else:
                btn.configure(fg=TEXT_DIM, bg=BG_SURFACE3)
        self.app._page = 1
        self.render()

    def _update_wl_count(self):
        n = len(STORE.wishlist)
        self.wl_lbl.configure(text=f"♥ {n} game(s) in Wishlist" if n else "")
