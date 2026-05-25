"""
ui/pages/detail_page.py
=======================
Halaman detail game: screenshot viewer, info panel, PC Requirements, dan Review tab.

Perubahan:
  - Platform & Tags dipindah ke bawah Description di tab Info
  - Screenshot hanya tampil saat tab "Info & Description" aktif
  - Tab PC Requirements dan Reviews menggunakan full-width tanpa screenshot
  - Tab Reviews: tampilkan review semua user + form tulis review sendiri
"""

import webbrowser
from io import BytesIO
from urllib.request import urlopen, Request

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox

from config.settings import COVER_W, COVER_H
from config.theme import (
    BG_DEEP, BG_PANEL, BG_CARD, BG_SURFACE2, BG_SURFACE3,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_BG, ACCENT_DIM,
    GREEN, GREEN_BG, GREEN_DIM, AMBER, AMBER_BG, RED_COL, RED_BG,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    FREE_GREEN, WARN_ORANGE,
    F, FM, divider, review_color, meta_color,
)
from store.local_store import STORE
from auth.session import SESSION
from utils.img_cache import IMG
from utils.helpers import parse_reqs

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

MAIN_W, MAIN_H   = 720, 405
THUMB_W, THUMB_H = 116, 65


class DetailPage(tk.Frame):
    """Frame halaman detail. Diisi ulang setiap kali game berbeda dibuka."""

    def __init__(self, master, parent_app):
        super().__init__(master, bg=BG_DEEP)
        self.app = parent_app
        self._thumb_refs   = []
        self._thumb_cells  = []
        self._current_game = None
        self._shot_container = None

    def load(self, game: dict):
        for w in self.winfo_children():
            w.destroy()
        self._thumb_refs     = []
        self._thumb_cells    = []
        self._current_game   = game
        self._shot_container = None
        self._build(game)

    # =========================================================================
    #  MAIN BUILDER
    # =========================================================================
    def _build(self, g: dict):
        outer = tk.Frame(self, bg=BG_DEEP)
        outer.pack(fill="both", expand=True)

        # Footer pinned bottom
        tk.Frame(outer, bg=BORDER2, height=1).pack(side="bottom", fill="x")
        foot = tk.Frame(outer, bg=BG_PANEL)
        foot.pack(side="bottom", fill="x")

        tk.Button(foot, text="<- Back", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=self.app._go_back).pack(side="left", padx=12, pady=10)
        if g["rawg_count"]:
            tk.Label(foot, text=f"{g['rawg_count']:,} ratings",
                     font=F(9), fg=TEXT_MUTED, bg=BG_PANEL).pack(side="left", padx=4)

        self._det_wl_var = tk.StringVar(
            value="Remove from Wishlist" if STORE.in_wl(g["slug"]) else "Add to Wishlist")
        tk.Button(foot, textvariable=self._det_wl_var, font=F(10), fg=AMBER, bg=AMBER_BG,
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=lambda: self._toggle_wl(g)).pack(side="right", padx=6, pady=10)

        has_price = g.get("is_free") or (g.get("price") not in ("N/A", "", None))
        if has_price:
            steam_url = (f"https://store.steampowered.com/app/{g['steam_appid']}"
                         if g.get("steam_appid") else
                         f"https://store.steampowered.com/search/?term={g['title'].replace(' ', '+')}")
            price_lbl = "FREE" if g.get("is_free") else g["price"]
            tk.Button(foot, text=f"Buy Now   {price_lbl}".strip(),
                      font=F(11, True), fg=TEXT_WHITE, bg=ACCENT,
                      activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                      padx=22, pady=8,
                      command=lambda url=steam_url: webbrowser.open(url)
                      ).pack(side="right", padx=4, pady=10)

        # Tab bar
        tk.Frame(outer, bg=BORDER2, height=1).pack(side="bottom", fill="x")
        tbar = tk.Frame(outer, bg=BG_PANEL)
        tbar.pack(side="bottom", fill="x")
        tk.Frame(outer, bg=BORDER2, height=1).pack(side="bottom", fill="x")

        self._dtab_btns = {}
        self._dtab_frms = {}

        # Tab content area
        self._dtcontent = tk.Frame(outer, bg=BG_DEEP)
        self._dtcontent.pack(side="bottom", fill="both", expand=True)

        for tid, tlabel in [("info",   "  Info & Description  "),
                             ("reqs",   "  PC Requirements  "),
                             ("review", "  Reviews  ")]:
            btn = tk.Button(tbar, text=tlabel, font=F(10), fg=TEXT_DIM, bg=BG_PANEL,
                            activebackground=BG_PANEL, activeforeground=TEXT_WHITE,
                            relief="flat", cursor="hand2", pady=11,
                            command=lambda t=tid: self._dtab(t))
            btn.pack(side="left")
            self._dtab_btns[tid] = btn

        self._dtab_frms["info"]   = self._frame_info(g)
        self._dtab_frms["reqs"]   = self._frame_reqs(g)
        self._dtab_frms["review"] = self._frame_review(g)

        # Top area
        top = tk.Frame(outer, bg=BG_DEEP)
        top.pack(fill="both", expand=True)

        # Right info panel
        info_panel = tk.Frame(top, bg=BG_PANEL, width=290)
        info_panel.pack(side="right", fill="y")
        info_panel.pack_propagate(False)
        tk.Frame(info_panel, bg=BORDER2, width=1).pack(side="left", fill="y")
        self._build_info_panel(info_panel, g)
        self._info_panel = info_panel
        self._top_frame  = top

        # Screenshot container (toggle by tab)
        self._shot_container = tk.Frame(top, bg=BG_DEEP)
        self._build_screenshot_area(self._shot_container, g)

        self._dtab("info")

    # =========================================================================
    #  RIGHT INFO PANEL
    # =========================================================================
    def _build_info_panel(self, parent, g):
        ip = tk.Frame(parent, bg=BG_PANEL)
        ip.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(ip, text=g["title"], font=F(13, True), fg=TEXT_WHITE, bg=BG_PANEL,
                 wraplength=260, justify="left").pack(anchor="w", pady=(0, 8))

        cv_thumb = tk.Canvas(ip, width=258, height=145, bg=g["color"], highlightthickness=0)
        cv_thumb.pack(anchor="w", pady=(0, 10))
        cv_thumb.create_text(129, 72, text=g["title"][0], font=F(26, True), fill=TEXT_MUTED)

        def _sc_thumb(img):
            if img:
                cv_thumb._img = img
                cv_thumb.delete("all")
                cv_thumb.create_image(0, 0, anchor="nw", image=img)

        IMG.get(g["cover_url"], size=(258, 145), cb=lambda img: self.after(0, _sc_thumb, img))

        divider(ip, pady=(0, 6))

        for label, val, col in [
            ("RECENT REVIEWS:", g.get("review") or "?",  review_color(g.get("review") or "")),
            ("RELEASE DATE:",   g.get("release_date") or "?", TEXT_WHITE),
            ("DEVELOPER:",      (g.get("developer") or "?")[:26], TEXT_WHITE),
            ("PUBLISHER:",      (g.get("publisher") or g.get("developer") or "?")[:26], TEXT_WHITE),
        ]:
            row = tk.Frame(ip, bg=BG_PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=F(8, True), fg=TEXT_DIM, bg=BG_PANEL,
                     anchor="w", width=15).pack(side="left")
            tk.Label(row, text=val, font=F(9), fg=col, bg=BG_PANEL,
                     anchor="w", wraplength=155, justify="left").pack(side="left")

        divider(ip, pady=(6, 6))

        sf = tk.Frame(ip, bg=BG_PANEL)
        sf.pack(anchor="w", pady=(0, 6))
        rb = tk.Frame(sf, bg=AMBER_BG, highlightthickness=1, highlightbackground="#2a1e06")
        rb.pack(side="left", padx=(0, 6))
        tk.Label(rb, text=f"* {g['rating']:.2f}", font=FM(11, True),
                 fg=AMBER, bg=AMBER_BG, padx=8, pady=4).pack(side="left")
        tk.Label(rb, text="RAWG", font=F(8), fg=TEXT_DIM, bg=AMBER_BG, padx=3).pack(side="left")
        if g.get("metacritic"):
            mb = tk.Frame(sf, bg=GREEN_BG, highlightthickness=1, highlightbackground=GREEN_DIM)
            mb.pack(side="left")
            tk.Label(mb, text=str(g["metacritic"]), font=FM(11, True),
                     fg=meta_color(g["metacritic"]), bg=GREEN_BG, padx=8, pady=4).pack(side="left")
            tk.Label(mb, text="MC", font=F(8), fg=TEXT_DIM, bg=GREEN_BG, padx=3).pack(side="left")

        pc_c = FREE_GREEN if g["is_free"] else ACCENT_LIGHT
        pc_b = GREEN_BG   if g["is_free"] else ACCENT_BG
        pc_x = GREEN_DIM  if g["is_free"] else ACCENT_DIM
        pb2 = tk.Frame(ip, bg=pc_b, highlightthickness=1, highlightbackground=pc_x)
        pb2.pack(anchor="w", pady=(0, 6))
        tk.Label(pb2, text=g["price"], font=FM(12, True), fg=pc_c, bg=pc_b, padx=10, pady=4).pack()

    # =========================================================================
    #  SCREENSHOT VIEWER
    # =========================================================================
    def _build_screenshot_area(self, parent, g):
        shots = g.get("screenshots") or []
        main_cv = tk.Canvas(parent, bg="#0a0a0a", highlightthickness=0)
        main_cv.pack(fill="both", expand=True)
        self._main_cv = main_cv

        if not shots:
            main_cv.create_text(360, 180, text="No screenshots available.",
                                font=F(11), fill=TEXT_DIM)
            return

        main_cv.create_text(360, 180, text="Loading...", font=F(11), fill=TEXT_MUTED)
        self._main_shot_url = shots[0]
        self._main_shot_idx = 0

        def _load_main(url, idx=0):
            self._main_shot_url = url
            self._main_shot_idx = idx
            for c in self._thumb_cells:
                try: c.configure(highlightbackground=BORDER2)
                except: pass
            if idx < len(self._thumb_cells):
                try: self._thumb_cells[idx].configure(highlightbackground=ACCENT)
                except: pass
            main_cv.delete("all")
            main_cv.create_text(main_cv.winfo_width() // 2 or 360,
                                main_cv.winfo_height() // 2 or 180,
                                text="Loading...", font=F(10), fill=TEXT_MUTED)

            def _show(img):
                if not img: return
                main_cv._main_img = img
                main_cv.delete("all")
                cw = main_cv.winfo_width() or MAIN_W
                ch = main_cv.winfo_height() or MAIN_H
                x = max(0, (cw - img.width()) // 2)
                y = max(0, (ch - img.height()) // 2)
                main_cv.create_image(x, y, anchor="nw", image=img)

            cw = main_cv.winfo_width() or MAIN_W
            ch = main_cv.winfo_height() or MAIN_H
            IMG.get(url, size=(cw, ch), cb=lambda img: self.after(0, _show, img))

        main_cv.bind("<Button-1>",
                     lambda e: self._open_lightbox(self._main_shot_url,
                                                    getattr(main_cv, "_main_img", None)))

        strip_bg = tk.Frame(parent, bg="#0d0d0d")
        strip_bg.pack(fill="x")
        strip_cv = tk.Canvas(strip_bg, bg="#0d0d0d", highlightthickness=0, height=THUMB_H + 14)
        strip_cv.pack(fill="x", pady=6, padx=6)
        strip_inner = tk.Frame(strip_cv, bg="#0d0d0d")
        strip_cv.create_window((0, 0), window=strip_inner, anchor="nw")
        strip_inner.bind("<Configure>", lambda e: strip_cv.configure(
            scrollregion=strip_cv.bbox("all")))
        strip_cv.bind("<MouseWheel>",
                      lambda e: strip_cv.xview_scroll(int(-1*(e.delta/120)), "units"))

        for idx, url in enumerate(shots):
            cell = tk.Frame(strip_inner, bg=BG_CARD, highlightthickness=2,
                            highlightbackground=ACCENT if idx == 0 else BORDER2,
                            cursor="hand2")
            cell.pack(side="left", padx=3)
            self._thumb_cells.append(cell)
            tc = tk.Canvas(cell, width=THUMB_W, height=THUMB_H, bg=BG_CARD,
                           highlightthickness=0, cursor="hand2")
            tc.pack()
            tc.create_text(THUMB_W//2, THUMB_H//2, text="...", font=F(8), fill=TEXT_MUTED)

            def _lt(img, c=tc, cl=cell, i=idx, u=url):
                if img:
                    self._thumb_refs.append(img)
                    c.delete("all")
                    c.create_image(0, 0, anchor="nw", image=img)
                    c.bind("<Button-1>", lambda e, _i=i, _u=u: _load_main(_u, _i))
                    cl.bind("<Button-1>", lambda e, _i=i, _u=u: _load_main(_u, _i))

            IMG.get(url, size=(THUMB_W, THUMB_H),
                    cb=lambda img, fn=_lt: self.after(0, fn, img))

        self.after(120, lambda: _load_main(shots[0], 0))

    def _open_lightbox(self, url, img_ref=None):
        lb = tk.Toplevel(self)
        lb.title("Preview")
        lb.configure(bg="#000000")
        lb.geometry("1100x650")
        lb.grab_set()
        lb.bind("<Escape>", lambda e: lb.destroy())
        hdr = tk.Frame(lb, bg="#0a0a0a")
        hdr.pack(fill="x")
        tk.Button(hdr, text="X  Close", font=F(10), fg=TEXT_DIM, bg="#0a0a0a",
                  relief="flat", cursor="hand2", padx=16, pady=8,
                  command=lb.destroy).pack(side="right")
        tk.Label(hdr, text="Screenshot Preview", font=F(10, True),
                 fg=TEXT_WHITE, bg="#0a0a0a").pack(side="left", padx=16, pady=8)
        tk.Frame(lb, bg=BORDER2, height=1).pack(fill="x")
        cv = tk.Canvas(lb, bg="#000000", highlightthickness=0)
        cv.pack(fill="both", expand=True)

        def _place(event=None):
            cw, ch = cv.winfo_width(), cv.winfo_height()
            if cw < 2 or ch < 2: return
            cv.delete("all")
            try:
                req  = Request(url, headers={"User-Agent": "BitScore/4.0"})
                data = urlopen(req, timeout=10).read()
                pil  = Image.open(BytesIO(data)).convert("RGB")
                pil.thumbnail((cw - 40, ch - 40), Image.LANCZOS)
                lb._lb_img = ImageTk.PhotoImage(pil)
                cv.create_image((cw - pil.width)//2, (ch - pil.height)//2,
                                anchor="nw", image=lb._lb_img)
            except Exception:
                cv.create_text(cw//2, ch//2, text="Could not load image.",
                               font=F(10), fill=TEXT_DIM)

        if PIL_AVAILABLE:
            cv.after(80, _place)
            cv.bind("<Configure>", lambda e: _place())
        elif img_ref:
            cv.after(80, lambda: cv.create_image(0, 0, anchor="nw", image=img_ref))

    # =========================================================================
    #  TAB SWITCHING  — screenshot hanya tampil di tab info
    # =========================================================================
    def _dtab(self, tid: str):
        import tkinter.font as tkfont
        for t, btn in self._dtab_btns.items():
            active = (t == tid)
            btn.configure(
                fg=TEXT_WHITE if active else TEXT_DIM,
                bg=BG_SURFACE2 if active else BG_PANEL,
                font=tkfont.Font(family="Segoe UI", size=10,
                                 weight="bold" if active else "normal"))

        for t, frm in self._dtab_frms.items():
            if t == tid:
                frm.pack(fill="both", expand=True)
            else:
                frm.pack_forget()

        # Tampilkan/sembunyikan area screenshot dan top panel
        if self._shot_container:
            if tid in ("info", "reqs"):
                # Show top frame (screenshots + info panel) above tab content
                if hasattr(self, "_top_frame"):
                    self._top_frame.pack(fill="both", expand=True)
                self._shot_container.pack(side="left", fill="both", expand=True)
                if hasattr(self, "_info_panel"):
                    self._info_panel.pack(side="right", fill="y")
                # Tab content gets fixed height at bottom
                self._dtcontent.pack_configure(expand=False)
                self._dtcontent.configure(height=280)
                self._dtcontent.pack_propagate(False)
            else:
                # Reviews tab: hide top frame, give full height to tab content
                self._shot_container.pack_forget()
                if hasattr(self, "_top_frame"):
                    self._top_frame.pack_forget()
                self._dtcontent.pack_propagate(True)
                self._dtcontent.pack_configure(expand=True)

    def _toggle_wl(self, g):
        STORE.toggle_wl(g["slug"])
        self._det_wl_var.set(
            "Remove from Wishlist" if STORE.in_wl(g["slug"]) else "Add to Wishlist")

    # =========================================================================
    #  TAB: INFO & DESCRIPTION
    # =========================================================================
    def _frame_info(self, g):
        frm = tk.Frame(self._dtcontent, bg=BG_DEEP)

        outer = tk.Frame(frm, bg=BG_DEEP)
        outer.pack(fill="both", expand=True)
        info_cv = tk.Canvas(outer, bg=BG_DEEP, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=info_cv.yview,
                            style="Dark.Vertical.TScrollbar")
        info_cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        info_cv.pack(side="left", fill="both", expand=True)
        cf = tk.Frame(info_cv, bg=BG_DEEP)
        cw_id = info_cv.create_window((0, 0), window=cf, anchor="nw")
        cf.bind("<Configure>", lambda e: info_cv.configure(scrollregion=info_cv.bbox("all")))

        def _mw(e): info_cv.yview_scroll(int(-1*(e.delta/120)), "units")
        info_cv.bind("<MouseWheel>", _mw)
        cf.bind("<MouseWheel>", _mw)

        def _on_resize(e):
            info_cv.itemconfig(cw_id, width=e.width)
            desc_lbl.configure(wraplength=max(200, e.width - 40))
        info_cv.bind("<Configure>", _on_resize)

        wrap = tk.Frame(cf, bg=BG_DEEP)
        wrap.pack(fill="x", padx=16, pady=(18, 10))

        # Description
        tk.Label(wrap, text="DESCRIPTION", font=F(8, True), fg=TEXT_MUTED,
                 bg=BG_DEEP).pack(anchor="w", pady=(0, 6))
        desc_text = g["description"] or "(No description available)"
        desc_lbl = tk.Label(wrap, text=desc_text, font=F(10), fg=TEXT_DIM, bg=BG_DEEP,
                            wraplength=700, justify="left")
        desc_lbl.pack(anchor="w", fill="x")
        desc_lbl.bind("<MouseWheel>", _mw)

        divider(wrap, pady=(14, 8))

        # Platform
        if g["platforms"]:
            tk.Label(wrap, text="PLATFORM", font=F(8, True), fg=TEXT_MUTED,
                     bg=BG_DEEP).pack(anchor="w", pady=(0, 6))
            plat_wrap = tk.Frame(wrap, bg=BG_DEEP)
            plat_wrap.pack(anchor="w", fill="x", pady=(0, 10))
            row_p = tk.Frame(plat_wrap, bg=BG_DEEP)
            row_p.pack(anchor="w")
            for i, p in enumerate(g["platforms"][:12]):
                if i > 0 and i % 6 == 0:
                    row_p = tk.Frame(plat_wrap, bg=BG_DEEP)
                    row_p.pack(anchor="w", pady=(4, 0))
                tk.Label(row_p, text=p, font=F(8), fg=TEXT_DIM, bg=BG_SURFACE3,
                         padx=8, pady=4).pack(side="left", padx=(0, 6), pady=2)

        # Tags
        if g["tags"]:
            tk.Label(wrap, text="TAGS", font=F(8, True), fg=TEXT_MUTED,
                     bg=BG_DEEP).pack(anchor="w", pady=(0, 6))
            tags_wrap = tk.Frame(wrap, bg=BG_DEEP)
            tags_wrap.pack(anchor="w", fill="x", pady=(0, 14))
            row_t = tk.Frame(tags_wrap, bg=BG_DEEP)
            row_t.pack(anchor="w")
            for i, tag in enumerate(g["tags"]):
                if i > 0 and i % 6 == 0:
                    row_t = tk.Frame(tags_wrap, bg=BG_DEEP)
                    row_t.pack(anchor="w", pady=(4, 0))
                tk.Label(row_t, text=tag, font=F(8), fg=ACCENT_LIGHT, bg=ACCENT_BG,
                         padx=7, pady=4).pack(side="left", padx=(0, 5), pady=1)

        return frm

    # =========================================================================
    #  TAB: PC REQUIREMENTS  (full width)
    # =========================================================================
    def _frame_reqs(self, g):
        frm = tk.Frame(self._dtcontent, bg=BG_DEEP)
        if not g.get("pc_minimum") and not g.get("pc_recommended"):
            tk.Label(frm, text="PC Requirements data not available.",
                     font=F(10), fg=TEXT_DIM, bg=BG_DEEP).pack(pady=40)
            return frm

        outer = tk.Frame(frm, bg=BG_DEEP)
        outer.pack(fill="both", expand=True)
        req_cv = tk.Canvas(outer, bg=BG_DEEP, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=req_cv.yview,
                            style="Dark.Vertical.TScrollbar")
        req_cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        req_cv.pack(side="left", fill="both", expand=True)
        cf = tk.Frame(req_cv, bg=BG_DEEP)
        cw_id = req_cv.create_window((0, 0), window=cf, anchor="nw")
        cf.bind("<Configure>", lambda e: req_cv.configure(scrollregion=req_cv.bbox("all")))
        req_cv.bind("<Configure>", lambda e: req_cv.itemconfig(cw_id, width=e.width))

        ICON_MAP = {
            "OS": "PC", "PROCESSOR": "CPU", "CPU": "CPU",
            "MEMORY": "RAM", "RAM": "RAM",
            "GRAPHICS": "GPU", "GPU": "GPU",
            "DIRECTX": "DX", "NETWORK": "NET",
            "STORAGE": "HDD", "HARD DRIVE": "HDD",
            "SOUND CARD": "SND", "AUDIO": "SND",
            "ADDITIONAL NOTES": "NOTE",
        }

        def _mw(e): req_cv.yview_scroll(int(-1*(e.delta/120)), "units")
        req_cv.bind("<MouseWheel>", _mw)
        cf.bind("<MouseWheel>", _mw)

        def _build_col(parent, title, raw_text, accent_col):
            if not raw_text: return
            parsed = parse_reqs(raw_text)
            if not parsed: return
            hdr = tk.Frame(parent, bg=BG_SURFACE3, highlightthickness=1,
                           highlightbackground=BORDER2)
            hdr.pack(fill="x")
            tk.Frame(hdr, bg=accent_col, width=4).pack(side="left", fill="y")
            tk.Label(hdr, text=title, font=F(11, True), fg=accent_col,
                     bg=BG_SURFACE3, pady=10, padx=14).pack(side="left", anchor="w")
            hdr.bind("<MouseWheel>", _mw)
            card = tk.Frame(parent, bg=BG_CARD, highlightthickness=1,
                            highlightbackground=BORDER2)
            card.pack(fill="both", expand=True)
            card.bind("<MouseWheel>", _mw)
            for idx, (key, val) in enumerate(parsed):
                bg = BG_CARD if idx % 2 == 0 else BG_SURFACE3
                row = tk.Frame(card, bg=bg)
                row.pack(fill="x")
                row.bind("<MouseWheel>", _mw)
                if key:
                    icon = ICON_MAP.get(key, ">")
                    kl = tk.Label(row, text=f"{icon}  {key}", font=F(9, True),
                                  fg=TEXT_DIM, bg=bg, anchor="w", width=16, pady=8)
                    kl.pack(side="left")
                    kl.bind("<MouseWheel>", _mw)
                    tk.Frame(row, bg=BORDER2, width=1).pack(side="left", fill="y", pady=6)
                    vl = tk.Label(row, text=val, font=F(9), fg=TEXT_WHITE, bg=bg,
                                  anchor="w", padx=10, pady=8, wraplength=400, justify="left")
                    vl.pack(side="left", fill="x", expand=True)
                    vl.bind("<MouseWheel>", _mw)
                else:
                    note = tk.Label(row, text=f"  {val}", font=F(8), fg=TEXT_MUTED, bg=bg,
                                    anchor="w", padx=12, pady=5, wraplength=600, justify="left")
                    note.pack(fill="x")
                    note.bind("<MouseWheel>", _mw)

        row_frame = tk.Frame(cf, bg=BG_DEEP)
        row_frame.pack(fill="x", padx=12, pady=12)
        has_min = bool(g.get("pc_minimum"))
        has_rec = bool(g.get("pc_recommended"))
        if has_min and has_rec:
            col_min = tk.Frame(row_frame, bg=BG_DEEP)
            col_min.pack(side="left", fill="both", expand=True, padx=(0, 6))
            tk.Frame(row_frame, bg=BORDER2, width=1).pack(side="left", fill="y", pady=4)
            col_rec = tk.Frame(row_frame, bg=BG_DEEP)
            col_rec.pack(side="left", fill="both", expand=True, padx=(6, 0))
            _build_col(col_min, "Minimum Requirements",     g.get("pc_minimum", ""),     AMBER)
            _build_col(col_rec, "Recommended Requirements", g.get("pc_recommended", ""), ACCENT_LIGHT)
        elif has_min:
            _build_col(row_frame, "Minimum Requirements",     g.get("pc_minimum", ""),     AMBER)
        else:
            _build_col(row_frame, "Recommended Requirements", g.get("pc_recommended", ""), ACCENT_LIGHT)
        return frm

    # =========================================================================
    #  TAB: REVIEWS  (full width + scrollable)
    #  - Tampilkan semua review dari semua user (dengan username)
    #  - Admin bisa hapus review siapapun
    #  - User bisa tulis/edit/hapus review sendiri
    # =========================================================================
    def _frame_review(self, g):
        frm = tk.Frame(self._dtcontent, bg=BG_DEEP)
        self._rv_frame = frm
        self._current_review_game = g
        self._render_review_tab()
        return frm

    def _render_review_tab(self):
        frm  = self._rv_frame
        g    = self._current_review_game
        slug = g["slug"]
        for w in frm.winfo_children():
            w.destroy()

        # Scrollable wrapper
        outer = tk.Frame(frm, bg=BG_DEEP)
        outer.pack(fill="both", expand=True)
        rv_cv = tk.Canvas(outer, bg=BG_DEEP, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=rv_cv.yview,
                            style="Dark.Vertical.TScrollbar")
        rv_cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        rv_cv.pack(side="left", fill="both", expand=True)
        cf = tk.Frame(rv_cv, bg=BG_DEEP)
        cw_id = rv_cv.create_window((0, 0), window=cf, anchor="nw")
        cf.bind("<Configure>", lambda e: rv_cv.configure(scrollregion=rv_cv.bbox("all")))
        rv_cv.bind("<Configure>", lambda e: rv_cv.itemconfig(cw_id, width=e.width))

        def _mw(e): rv_cv.yview_scroll(int(-1*(e.delta/120)), "units")
        rv_cv.bind("<MouseWheel>", _mw)
        cf.bind("<MouseWheel>", _mw)

        body = tk.Frame(cf, bg=BG_DEEP)
        body.pack(fill="x", padx=20, pady=14)

        lmap = {1: "Poor", 2: "Fair", 3: "Average", 4: "Good", 5: "Outstanding!"}
        me   = SESSION.username

        # ── Tampilkan semua review dari semua user ────────────────────────────
        all_reviews = STORE.get_reviews(slug)
        if all_reviews:
            tk.Label(body, text=f"REVIEWS  ({len(all_reviews)})", font=F(9, True),
                     fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 8))

            for rv in all_reviews:
                uname = rv.get("username", "?")
                score = rv.get("score", 0)
                is_mine = (uname.lower() == me.lower())

                card = tk.Frame(body, bg=BG_CARD, highlightthickness=1,
                                highlightbackground=BORDER2)
                card.pack(fill="x", pady=(0, 8))
                card.bind("<MouseWheel>", _mw)

                # Header row: username + bintang + tanggal
                hd = tk.Frame(card, bg=BG_CARD)
                hd.pack(fill="x", padx=12, pady=(10, 4))

                # Username badge
                badge_bg = ACCENT_BG if is_mine else BG_SURFACE3
                badge_fg = ACCENT_LIGHT if is_mine else TEXT_DIM
                tk.Label(hd, text=f"  {uname}  ", font=F(9, True),
                         fg=badge_fg, bg=badge_bg, padx=4, pady=2).pack(side="left")
                if is_mine:
                    tk.Label(hd, text="(kamu)", font=F(8), fg=TEXT_MUTED,
                             bg=BG_CARD).pack(side="left", padx=4)

                # Stars
                sf = tk.Frame(hd, bg=BG_CARD)
                sf.pack(side="left", padx=10)
                for i in range(1, 6):
                    tk.Label(sf, text="★", font=F(12),
                             fg=AMBER if i <= score else TEXT_MUTED,
                             bg=BG_CARD).pack(side="left")
                tk.Label(hd, text=lmap.get(score, ""), font=F(9, True),
                         fg=AMBER, bg=BG_CARD).pack(side="left", padx=4)

                # Date
                tk.Label(hd, text=rv.get("date", ""), font=F(8),
                         fg=TEXT_MUTED, bg=BG_CARD).pack(side="right")

                # Review text
                if rv.get("text"):
                    divider(card, padx=12, pady=0)
                    txt_lbl = tk.Label(card, text=rv["text"], font=F(10), fg=TEXT_WHITE,
                                       bg=BG_CARD, wraplength=820, justify="left",
                                       padx=12, pady=8)
                    txt_lbl.pack(anchor="w")
                    txt_lbl.bind("<MouseWheel>", _mw)

                # Action buttons
                act = tk.Frame(card, bg=BG_CARD)
                act.pack(anchor="e", padx=12, pady=(0, 8))
                if is_mine:
                    tk.Button(act, text="Hapus Review Saya", font=F(9), fg=RED_COL, bg=RED_BG,
                              relief="flat", cursor="hand2", padx=10, pady=4,
                              command=lambda u=uname: self._del_review(slug, u)).pack(side="left")
                elif SESSION.is_admin:
                    tk.Button(act, text=f"Hapus Review ({uname})", font=F(9), fg=RED_COL, bg=RED_BG,
                              relief="flat", cursor="hand2", padx=10, pady=4,
                              command=lambda u=uname: self._del_review(slug, u)).pack(side="left")

            divider(body, pady=(8, 8))
        else:
            tk.Label(body, text="Belum ada review untuk game ini.", font=F(10),
                     fg=TEXT_DIM, bg=BG_DEEP).pack(anchor="w", pady=(0, 12))

        # ── Form tulis/edit review milik user saat ini ────────────────────────
        # Jika guest → tampilkan notifikasi & tombol login, bukan form review
        if SESSION.current_user and SESSION.current_user.is_guest():
            guest_box = tk.Frame(body, bg=BG_SURFACE3, highlightthickness=1,
                                 highlightbackground=BORDER2)
            guest_box.pack(fill="x", pady=(12, 0))

            tk.Label(guest_box, text="🔒  Login untuk melakukan review",
                     font=F(11, True), fg=TEXT_WHITE, bg=BG_SURFACE3,
                     pady=14).pack()
            tk.Label(guest_box, text="Kamu masuk sebagai Guest. Buat akun atau login\n"
                                     "untuk bisa menulis review dan memberi rating.",
                     font=F(9), fg=TEXT_DIM, bg=BG_SURFACE3,
                     justify="center").pack(pady=(0, 10))
            tk.Button(guest_box, text="  Login / Daftar  ",
                      font=F(11, True), fg=TEXT_WHITE, bg=ACCENT,
                      activebackground=ACCENT_LIGHT, relief="flat",
                      cursor="hand2", padx=20, pady=10,
                      command=self._open_login_popup).pack(pady=(0, 16))
            return

        my_rv = STORE.get_user_review(slug, me)

        if my_rv:
            tk.Label(body, text="EDIT REVIEW KAMU", font=F(8, True),
                     fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(4, 6))
        else:
            tk.Label(body, text="TULIS REVIEW KAMU", font=F(10, True),
                     fg=TEXT_WHITE, bg=BG_DEEP).pack(anchor="w", pady=(4, 4))

        score_var = tk.IntVar(value=my_rv.get("score", 0) if my_rv else 0)

        tk.Label(body, text="RATING", font=F(8, True), fg=TEXT_MUTED,
                 bg=BG_DEEP).pack(anchor="w", pady=(8, 4))
        star_row  = tk.Frame(body, bg=BG_DEEP)
        star_row.pack(anchor="w")
        star_btns = []
        star_lbl  = tk.Label(star_row, font=F(10), fg=AMBER, bg=BG_DEEP)

        def _draw_stars(v):
            for i, b in enumerate(star_btns, 1):
                b.configure(fg=AMBER if i <= v else TEXT_MUTED)
            lmap2 = {0: "pilih bintang...", 1: "Poor", 2: "Fair",
                     3: "Average", 4: "Good", 5: "Outstanding!"}
            star_lbl.configure(text=lmap2.get(v, ""))

        def _set_star(v):
            score_var.set(v)
            _draw_stars(v)

        for i in range(1, 6):
            b = tk.Button(star_row, text="★", font=F(22), bg=BG_DEEP,
                          relief="flat", cursor="hand2",
                          activebackground=BG_DEEP, activeforeground=AMBER,
                          command=lambda v=i: _set_star(v))
            b.pack(side="left", padx=2)
            b.bind("<Enter>", lambda e, v=i: _draw_stars(v))
            b.bind("<Leave>", lambda e: _draw_stars(score_var.get()))
            star_btns.append(b)
        star_lbl.pack(side="left", padx=12)
        _draw_stars(score_var.get())

        tk.Label(body, text="KOMENTAR (opsional)", font=F(8, True),
                 fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(12, 4))
        tf = tk.Frame(body, bg=BG_SURFACE3, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=ACCENT)
        tf.pack(fill="x")
        txt_w = tk.Text(tf, font=F(10), fg=TEXT_WHITE, bg=BG_SURFACE3,
                        relief="flat", wrap="word", highlightthickness=0,
                        padx=12, pady=10, insertbackground=TEXT_WHITE, height=4)
        txt_w.pack(fill="x")
        txt_w.bind("<MouseWheel>", _mw)
        if my_rv and my_rv.get("text"):
            txt_w.insert("1.0", my_rv["text"])

        def _save():
            if not score_var.get():
                msgbox.showerror("Error", "Pilih rating bintang terlebih dahulu!", parent=self)
                return
            STORE.set_rv(slug, score_var.get(), txt_w.get("1.0", "end").strip(),
                         username=me)
            self._render_review_tab()

        btn_row = tk.Frame(body, bg=BG_DEEP)
        btn_row.pack(anchor="w", pady=(14, 24))
        tk.Button(btn_row, text="  Kirim Review  ",
                  font=F(12, True), fg=TEXT_WHITE, bg=ACCENT,
                  activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                  padx=20, pady=10, command=_save).pack(side="left")

    def _open_login_popup(self):
        """Buka popup login untuk guest. Jika berhasil login, refresh tab review."""
        from auth.login_page import LoginPage
        from store.user_store import USER_STORE
        from models.user import Role
        import tkinter.messagebox as mb

        popup = tk.Toplevel(self)
        popup.title("BitScore — Login")
        popup.geometry("440x640")
        popup.resizable(False, False)
        popup.configure(bg=BG_DEEP)
        popup.grab_set()   # modal: blokir window utama selama popup terbuka

        # Pusatkan popup relatif ke window detail
        self.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width()  - 440) // 2
        py = self.winfo_rooty() + (self.winfo_height() - 640) // 2
        popup.geometry(f"440x640+{px}+{py}")

        # ── Bangun UI login di dalam Toplevel ────────────────────────────────
        from config.theme import (
            BG_PANEL, BG_CARD, BG_SURFACE2, BG_SURFACE3,
            BORDER2, ACCENT_LIGHT, ACCENT_DIM, ACCENT_BG,
            GREEN, GREEN_BG, RED_COL, RED_BG,
            TEXT_WHITE, TEXT_DIM, TEXT_MUTED, AMBER,
            divider,
        )

        tk.Frame(popup, bg=ACCENT, height=4).pack(fill="x")
        wrap = tk.Frame(popup, bg=BG_DEEP)
        wrap.pack(fill="both", expand=True, padx=40, pady=30)

        # Logo
        logo_f = tk.Frame(wrap, bg=BG_DEEP)
        logo_f.pack(pady=(10, 4))
        tk.Label(logo_f, text="B", font=F(28, True), fg=ACCENT_LIGHT, bg=BG_DEEP).pack(side="left")
        tk.Label(logo_f, text="itScore", font=F(28, True), fg=TEXT_WHITE, bg=BG_DEEP).pack(side="left")
        tk.Label(wrap, text="Login untuk menulis review", font=F(10),
                 fg=TEXT_MUTED, bg=BG_DEEP).pack()

        divider(wrap, pady=16)

        mode_var = tk.StringVar(value="login")

        # Tab
        tab_f = tk.Frame(wrap, bg=BG_SURFACE3, highlightthickness=1,
                         highlightbackground=BORDER2)
        tab_f.pack(fill="x", pady=(0, 16))
        tab_login = tk.Button(tab_f, text="Login", font=F(10), fg=TEXT_WHITE,
                              bg=ACCENT, relief="flat", cursor="hand2", pady=8)
        tab_login.pack(side="left", fill="x", expand=True)
        tab_reg = tk.Button(tab_f, text="Daftar", font=F(10), fg=TEXT_DIM,
                            bg=BG_SURFACE3, relief="flat", cursor="hand2", pady=8)
        tab_reg.pack(side="left", fill="x", expand=True)

        form_f  = tk.Frame(wrap, bg=BG_DEEP)
        form_f.pack(fill="x")
        status_lbl = tk.Label(wrap, text="", font=F(9), fg=RED_COL,
                              bg=BG_DEEP, wraplength=340, justify="center")
        status_lbl.pack(pady=(6, 0))

        user_var = tk.StringVar()
        pass_var = tk.StringVar()
        conf_var = tk.StringVar()

        def _build_form():
            for w in form_f.winfo_children():
                w.destroy()
            # Username
            tk.Label(form_f, text="USERNAME", font=F(8, True),
                     fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 4))
            uf = tk.Frame(form_f, bg=BG_SURFACE3, highlightthickness=1,
                          highlightbackground=BORDER2)
            uf.pack(fill="x", pady=(0, 12))
            tk.Entry(uf, textvariable=user_var, font=F(11), fg=TEXT_WHITE,
                     bg=BG_SURFACE3, insertbackground=TEXT_WHITE,
                     relief="flat", highlightthickness=0).pack(fill="x", padx=10, ipady=8)
            # Password
            tk.Label(form_f, text="PASSWORD", font=F(8, True),
                     fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 4))
            pf = tk.Frame(form_f, bg=BG_SURFACE3, highlightthickness=1,
                          highlightbackground=BORDER2)
            pf.pack(fill="x", pady=(0, 4))
            pe = tk.Entry(pf, textvariable=pass_var, show="●", font=F(11),
                          fg=TEXT_WHITE, bg=BG_SURFACE3,
                          insertbackground=TEXT_WHITE, relief="flat",
                          highlightthickness=0)
            pe.pack(side="left", fill="x", expand=True, padx=10, ipady=8)
            # Konfirmasi (hanya register)
            if mode_var.get() == "register":
                tk.Label(form_f, text="KONFIRMASI PASSWORD", font=F(8, True),
                         fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(10, 4))
                cf = tk.Frame(form_f, bg=BG_SURFACE3, highlightthickness=1,
                              highlightbackground=BORDER2)
                cf.pack(fill="x")
                tk.Entry(cf, textvariable=conf_var, show="●", font=F(11),
                         fg=TEXT_WHITE, bg=BG_SURFACE3,
                         insertbackground=TEXT_WHITE, relief="flat",
                         highlightthickness=0).pack(fill="x", padx=10, ipady=8)

        def _switch(mode):
            mode_var.set(mode)
            status_lbl.configure(text="")
            if mode == "login":
                tab_login.configure(fg=TEXT_WHITE, bg=ACCENT)
                tab_reg.configure(fg=TEXT_DIM, bg=BG_SURFACE3)
                submit_btn.configure(text="Masuk")
            else:
                tab_reg.configure(fg=TEXT_WHITE, bg=ACCENT)
                tab_login.configure(fg=TEXT_DIM, bg=BG_SURFACE3)
                submit_btn.configure(text="Daftar Sekarang")
            _build_form()

        tab_login.configure(command=lambda: _switch("login"))
        tab_reg.configure(command=lambda: _switch("register"))

        submit_btn = tk.Button(wrap, font=F(12, True), fg=TEXT_WHITE, bg=ACCENT,
                               activebackground=ACCENT_LIGHT, relief="flat",
                               cursor="hand2", pady=12, text="Masuk")
        submit_btn.pack(fill="x", pady=(12, 0))

        def _submit():
            username = user_var.get().strip()
            password = pass_var.get().strip()
            status_lbl.configure(text="", fg=RED_COL)
            if not username or not password:
                status_lbl.configure(text="Username dan password tidak boleh kosong.")
                return
            if mode_var.get() == "login":
                user = USER_STORE.authenticate(username, password)
                if not user:
                    status_lbl.configure(text="Username atau password salah.")
                    return
                SESSION.login(user)
                popup.destroy()
                # Refresh badge username di header app utama
                app_root = self.winfo_toplevel()
                if hasattr(app_root, "_refresh_user_badge"):
                    app_root._refresh_user_badge()
                # Refresh tab review agar form muncul
                self._render_review_tab()
            else:
                confirm = conf_var.get().strip()
                if password != confirm:
                    status_lbl.configure(text="Password dan konfirmasi tidak cocok.")
                    return
                if len(password) < 6:
                    status_lbl.configure(text="Password minimal 6 karakter.")
                    return
                if len(username) < 3:
                    status_lbl.configure(text="Username minimal 3 karakter.")
                    return
                ok = USER_STORE.add(username, password, Role.USER)
                if not ok:
                    status_lbl.configure(text=f"Username '{username}' sudah dipakai.")
                    return
                status_lbl.configure(text="Akun dibuat! Silakan login.", fg=GREEN)
                _switch("login")
                user_var.set(username)

        submit_btn.configure(command=_submit)
        popup.bind("<Return>", lambda e: _submit())
        _build_form()

    def _del_review(self, slug, username=None):
        who = f" oleh {username}" if username else ""
        if msgbox.askyesno("Hapus Review", f"Yakin hapus review{who}?", parent=self):
            STORE.del_rv(slug, username=username)
            self._render_review_tab()