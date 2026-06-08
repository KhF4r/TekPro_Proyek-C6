"""
ui/app.py
=========
BitScoreApp: root window dan orkestrator navigasi antar halaman.
Bertanggung jawab atas:
  - Header (logo, nav tabs, search, tombol scrape)
  - State global (games, sort, filter, page)
  - Routing: home ↔ detail ↔ spec
  - Scraping (background thread)
"""

import math
import threading
import tkinter as tk
import tkinter.messagebox as msgbox

from config.settings import PAGE_SIZE, MAX_SCRAPE, LATEST_JSON, log
from config.theme import (
    BG_DEEP, BG_PANEL, BG_SURFACE2, BG_SURFACE3,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_DIM,
    RED_COL, RED_BG, AMBER,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    F,
)
from models.mapper import load_json, games_to_ui
from store.local_store import STORE
from auth.session import SESSION
from auth.guard import guard_admin
from UI.pages.home_page import HomePage
from UI.pages.detail_page import DetailPage
from UI.pages.spec_page import SpecPage
from UI.pages.admin_page import AdminPage
from UI.components.dialogs import ScrapeDialog

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

NAV_TABS = ["All Games", "Wishlist", "Reviews", "Spec Recommender"]


class BitScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BitScore — Game Ratings v4")
        self.geometry("1280x800")
        self.minsize(960, 640)
        self.configure(bg=BG_DEEP)
        self.resizable(True, True)

        # Flag logout: True = kembali ke login, False = tutup aplikasi sepenuhnya
        self._want_logout = False

        # ── Global state ──────────────────────────────────────────────────────
        self.games: list         = []
        self.search_var          = tk.StringVar()
        self.sort_by             = tk.StringVar(value="Metacritic")
        self.sort_dir            = "desc"
        self.active_genres: set  = set()
        self._active_nav         = tk.StringVar(value="All Games")
        self._active_platform    = tk.StringVar(value="All Platforms")
        self._page               = 1
        self._history: list      = []
        self._scraping           = False
        self._sort_popup         = None

        self._build_shell()
        self._show_page("home")

        if LATEST_JSON.exists():
            self._load_file(LATEST_JSON, silent=True)
        else:
            self.home_page.render()

        self.search_var.trace_add("write", self._on_search)
        self.bind_all("<MouseWheel>", self._route_scroll)

    # ══════════════════════════════════════════════════════════════════════════
    #  SHELL: header + body
    # ══════════════════════════════════════════════════════════════════════════
    def _build_shell(self):
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        # Header
        hdr = tk.Frame(self, bg=BG_PANEL, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        logo_f = tk.Frame(hdr, bg=BG_PANEL)
        logo_f.pack(side="left", padx=16, pady=10)
        self._back_btn = tk.Button(logo_f, text="←", font=F(14), fg=TEXT_DIM, bg=BG_PANEL,
                                   relief="flat", cursor="hand2", padx=6,
                                   command=self._go_back)
        self._back_btn.pack(side="left")
        tk.Label(logo_f, text="B",       font=F(20, True), fg=ACCENT_LIGHT, bg=BG_PANEL).pack(side="left")
        tk.Label(logo_f, text="itScore", font=F(20, True), fg=TEXT_WHITE,   bg=BG_PANEL).pack(side="left")

        # Nav tabs
        self._nav_frame = tk.Frame(hdr, bg=BG_PANEL)
        self._nav_frame.pack(side="left", padx=20)
        self._nav_btns = {}
        for tab in NAV_TABS:
            btn = tk.Button(self._nav_frame, text=tab, font=F(10), fg=TEXT_DIM, bg=BG_PANEL,
                            relief="flat", cursor="hand2", activebackground=BG_PANEL,
                            activeforeground=TEXT_WHITE, padx=12, pady=16,
                            command=lambda t=tab: self._switch_nav(t))
            btn.pack(side="left")
            self._nav_btns[tab] = btn
        self._update_nav_btns()

        # Search bar
        sr = tk.Frame(hdr, bg=BG_SURFACE3, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=ACCENT)
        sr.pack(side="left", pady=14, ipady=1)
        self.se = tk.Entry(sr, textvariable=self.search_var, font=F(10),
                           fg=TEXT_DIM, bg=BG_SURFACE3, insertbackground=TEXT_WHITE,
                           relief="flat", highlightthickness=0, width=24)
        self.se.pack(side="left", padx=(8, 0), pady=4)
        self.se.insert(0, "Search games...")
        self.se.bind("<FocusIn>",  self._si)
        self.se.bind("<FocusOut>", self._so)
        self.se.bind("<Return>",   lambda e: self.home_page.render())
        tk.Label(sr, text="⌕", font=F(12), fg=TEXT_DIM, bg=BG_SURFACE3).pack(side="right", padx=8)

        # Scrape button — hanya untuk admin
        if SESSION.is_admin:
            tk.Button(hdr, text="Scrape", font=F(10, True), fg=TEXT_WHITE, bg=ACCENT,
                      activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                      padx=14, command=self._open_scrape).pack(side="right", padx=(0, 14), pady=14)

        # Logout
        tk.Button(hdr, text="Logout", font=F(9), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=10, pady=6,
                  command=self._logout).pack(side="right", padx=(0, 6), pady=14)

        # Admin panel button (hanya muncul jika is_admin)
        if SESSION.is_admin:
            tk.Button(hdr, text="⚙  Admin", font=F(9, True),
                      fg=RED_COL, bg=RED_BG,
                      relief="flat", cursor="hand2", padx=12, pady=6,
                      command=self._open_admin).pack(side="right", padx=(0, 6), pady=14)

        # Username + role badge (disimpan referensinya agar bisa di-refresh)
        self._user_badge_anchor = tk.Frame(hdr, bg=BG_PANEL)
        self._user_badge_anchor.pack(side="right", padx=(0, 8), pady=14)
        self._refresh_user_badge()

        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")

        # Body
        self._body = tk.Frame(self, bg=BG_DEEP)
        self._body.pack(fill="both", expand=True)

        # Pages
        self.home_page   = HomePage(self._body, self)
        self.detail_page = DetailPage(self._body, self)
        self.spec_page   = SpecPage(self._body, self)
        self.admin_page  = AdminPage(self._body, self)

        self._pages = {
            "home":   self.home_page,
            "detail": self.detail_page,
            "spec":   self.spec_page,
            "admin":  self.admin_page,
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE NAVIGATION
    # ══════════════════════════════════════════════════════════════════════════
    def _show_page(self, name: str):
        for pname, pframe in self._pages.items():
            if pname == name:
                pframe.pack(fill="both", expand=True)
            else:
                pframe.pack_forget()

        if name == "home":
            self._nav_frame.pack(side="left", padx=20)
            self._back_btn.configure(fg=TEXT_MUTED, state="disabled")
        else:
            self._nav_frame.pack_forget()
            self._back_btn.configure(fg=TEXT_WHITE, state="normal")

    def _go_back(self):
        if self._history:
            prev = self._history.pop()
            self._show_page(prev)
        else:
            self._show_page("home")

    def _open_detail(self, game: dict):
        self._history.append("home")
        self.detail_page.load(game)
        self._show_page("detail")

    def _open_admin(self):
        if not guard_admin(self):
            return
        self._history.append("home")
        self.admin_page._switch_tab("users")
        self._show_page("admin")

    # ══════════════════════════════════════════════════════════════════════════
    def _refresh_user_badge(self):
        """Hapus dan rebuild widget username+role di header sesuai SESSION aktif."""
        anchor = self._user_badge_anchor
        for w in anchor.winfo_children():
            w.destroy()

        if SESSION.current_user and SESSION.current_user.is_guest():
            role_label = "GUEST"
            role_color = AMBER
        elif SESSION.is_admin:
            role_label = "ADMIN"
            role_color = RED_COL
        else:
            role_label = "USER"
            role_color = ACCENT_LIGHT

        user_f = tk.Frame(anchor, bg=BG_SURFACE3, highlightthickness=1,
                          highlightbackground=BORDER2)
        user_f.pack()
        tk.Label(user_f, text=f"  {SESSION.username}  ", font=F(9),
                 fg=TEXT_WHITE, bg=BG_SURFACE3, pady=6).pack(side="left")
        badge_f = tk.Frame(user_f, bg=role_color)
        badge_f.pack(side="left")
        tk.Label(badge_f, text=f" {role_label} ", font=F(8, True),
                 fg=BG_DEEP, bg=role_color, pady=6).pack()

    #  AUTH
    # ══════════════════════════════════════════════════════════════════════════
    def _logout(self):
        if not msgbox.askyesno("Logout", f"Logout dari akun '{SESSION.username}'?", parent=self):
            return
        SESSION.logout()
        self._want_logout = True   # sinyal ke main.py → kembali ke halaman login
        self.destroy()

    # ══════════════════════════════════════════════════════════════════════════
    #  NAV TABS
    # ══════════════════════════════════════════════════════════════════════════
    def _switch_nav(self, tab):
        if tab == "Spec Recommender":
            self._history.append("home")
            self._show_page("spec")
            return
        self._active_nav.set(tab)
        self._page = 1
        self._update_nav_btns()
        self.home_page.render()

    def _update_nav_btns(self):
        active = self._active_nav.get()
        for tab, btn in self._nav_btns.items():
            btn.configure(
                fg=TEXT_WHITE if tab == active else TEXT_DIM,
                bg=BG_SURFACE2 if tab == active else BG_PANEL,
            )

    # ══════════════════════════════════════════════════════════════════════════
    #  FILTERING & SORTING  (used by HomePage)
    # ══════════════════════════════════════════════════════════════════════════
    def _filtered(self) -> list:
        tab = self._active_nav.get()
        q   = self.search_var.get().strip().lower()
        if q in ("", "search games..."): q = ""

        if tab == "Wishlist":
            games = [g for g in self.games if STORE.in_wl(g["slug"])]
        elif tab == "Reviews":
            games = [g for g in self.games if STORE.has_rv(g["slug"])]
        else:
            games = list(self.games)

        if self.active_genres:
            games = [g for g in games if any(ge in g["genres"] for ge in self.active_genres)]

        plat = self._active_platform.get()
        PC_NAMES = {"PC", "Windows", "macOS", "Linux", "Mac"}
        if plat == "PC":
            games = [g for g in games if any(p in PC_NAMES for p in g["platforms"])]
        elif plat == "Other Platforms":
            games = [g for g in games if not any(p in PC_NAMES for p in g["platforms"])]

        reverse = (self.sort_dir == "desc")
        if self.sort_by.get() == "Name":
            games.sort(key=lambda g: g["title"].lower(), reverse=reverse)
        else:
            # Tiebreaker: 1) metacritic  2) rawg_rating  3) judul alfabet
            if reverse:
                games.sort(key=lambda g: (
                    -(g.get("metacritic") or 0),
                    -(g.get("rawg_rating") or 0.0),
                    g["title"].lower()
                ))
            else:
                games.sort(key=lambda g: (
                    (g.get("metacritic") or 0),
                    (g.get("rawg_rating") or 0.0),
                    g["title"].lower()
                ))

        for i, g in enumerate(games, 1):
            g["_rank"] = i

        if q:
            games = [g for g in games if q in g["title"].lower()]

        return games

    def _toggle_genre(self, g):
        hp = self.home_page
        if g in self.active_genres:
            self.active_genres.discard(g)
            hp.genre_btns[g].configure(fg=TEXT_DIM, bg=BG_SURFACE3)
        else:
            self.active_genres.add(g)
            hp.genre_btns[g].configure(fg=TEXT_WHITE, bg=ACCENT)
        self._page = 1
        hp.render()

    def _refresh_genres(self):
        genres: set = set()
        for g in self.games:
            genres.update(g["genres"])
        ordered = [g for g in ["Action", "Adventure", "RPG", "Horror",
                                "Simulation", "Racing", "Arcade", "Sports"]
                   if g in genres]
        self.active_genres.clear()
        self.home_page.refresh_genres(ordered)

    # ══════════════════════════════════════════════════════════════════════════
    #  SORT POPUP
    # ══════════════════════════════════════════════════════════════════════════
    def _open_sort_popup(self):
        if self._sort_popup:
            self._close_sort()
            return
        pop = tk.Toplevel(self)
        pop.overrideredirect(True)
        pop.configure(bg=BG_PANEL)
        self._sort_popup = pop
        tk.Frame(pop, bg=ACCENT, height=2).pack(fill="x")
        x = self.winfo_x() + self.winfo_width() - 260
        y = self.winfo_y() + 62
        pop.geometry(f"160x88+{x}+{y}")
        for opt in ["Metacritic", "Name"]:
            tk.Button(pop, text=opt, font=F(10), fg=TEXT_WHITE, bg=BG_PANEL,
                      activebackground=ACCENT, activeforeground=TEXT_WHITE,
                      relief="flat", cursor="hand2", anchor="w", padx=14,
                      command=lambda o=opt: self._sel_sort(o)).pack(fill="x", ipady=8)
            tk.Frame(pop, bg=BORDER2, height=1).pack(fill="x")
        pop.bind("<FocusOut>", lambda e: self._close_sort())
        pop.focus_set()

    def _close_sort(self):
        if self._sort_popup:
            self._sort_popup.destroy()
            self._sort_popup = None

    def _sel_sort(self, opt):
        self.sort_by.set(opt)
        arrow = "↑" if self.sort_dir == "asc" else "↓"
        self.home_page.sort_btn.configure(text=f"{opt}  {arrow}")
        self._close_sort()
        self._page = 1
        self.home_page.render()

    # ══════════════════════════════════════════════════════════════════════════
    #  SEARCH
    # ══════════════════════════════════════════════════════════════════════════
    def _on_search(self, *_):
        self._page = 1
        self.home_page.render()

    def _si(self, e):
        if self.search_var.get() == "Search games...":
            self.se.delete(0, "end")
            self.se.configure(fg=TEXT_WHITE)

    def _so(self, e):
        if not self.search_var.get():
            self.se.insert(0, "Search games...")
            self.se.configure(fg=TEXT_DIM)

    # ══════════════════════════════════════════════════════════════════════════
    #  SCRAPING
    # ══════════════════════════════════════════════════════════════════════════
    def _open_scrape(self):
        if self._scraping:
            msgbox.showinfo("Info", "Scraping in progress...")
            return
        if not REQUESTS_AVAILABLE:
            msgbox.showerror("Error", "pip install requests python-dotenv")
            return
        ScrapeDialog(self, self._run_scrape)

    def _run_scrape(self, mode, value):
        self._scraping = True
        self.home_page.status_lbl.configure(text="Scraping...")

        def worker():
            try:
                from scrapers.pipeline import Pipeline
                pipe = Pipeline()

                def cb(i, total, name):
                    self.after(0, self.home_page.status_lbl.configure,
                               {"text": f"[{i}/{total}] {name[:26]}..."})

                if mode == "top":
                    count = min(int(value) if value.isdigit() else 25, MAX_SCRAPE)
                    games = pipe.run_top(count=count, cb=cb)
                else:
                    games = pipe.run_search(query=value, count=25, cb=cb)
                self.after(0, self._scrape_done, games_to_ui(games), len(games))
            except Exception as e:
                self.after(0, self._scrape_err, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _scrape_done(self, ui, count):
        self._scraping = False
        self.games = ui
        self.home_page.status_lbl.configure(text=f"✓ {count} games scraped")
        self.after(5000, lambda: self.home_page.status_lbl.configure(text=""))
        self._refresh_genres()
        self._page = 1
        self.home_page.render()

    def _scrape_err(self, err):
        self._scraping = False
        self.home_page.status_lbl.configure(text="✗ Failed")
        self.after(5000, lambda: self.home_page.status_lbl.configure(text=""))
        msgbox.showerror("Error", f"Scraping failed:\n\n{err}")

    # ══════════════════════════════════════════════════════════════════════════
    #  DATA LOADING
    # ══════════════════════════════════════════════════════════════════════════
    def _load_file(self, path, silent=False):
        try:
            self.games = load_json(path)
        except Exception as e:
            if not silent:
                msgbox.showerror("Error", f"Failed to read file:\n{e}")
            return
        self._refresh_genres()
        self.home_page.render()

    # ══════════════════════════════════════════════════════════════════════════
    #  SCROLL ROUTING
    # ══════════════════════════════════════════════════════════════════════════
    def _route_scroll(self, e):
        try:
            focused = self.focus_get()
            if focused and str(focused) != str(self):
                top = focused.winfo_toplevel()
                if top is not self:
                    return
        except Exception:
            pass

        if self._pages.get("spec") and self._pages["spec"].winfo_ismapped():
            if hasattr(self.spec_page, "spec_cvlist"):
                self.spec_page.spec_cvlist.yview_scroll(int(-1 * (e.delta / 120)), "units")
            return

        if hasattr(self.home_page, "_scroll_fn"):
            self.home_page._scroll_fn(e)