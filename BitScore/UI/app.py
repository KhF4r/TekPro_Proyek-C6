"""
ui/app.py
---------
BitScoreApp — jendela utama aplikasi. Mengorkestrasikan UI, scraping,
filter, sort, dan navigasi detail.
"""

import threading
import tkinter as tk
import tkinter.messagebox as msgbox
from datetime import datetime
from pathlib import Path

from config.settings import (
    RAWG_API_KEY, OUTPUT_DIR, LATEST_JSON, REQUESTS_AVAILABLE,
)
from config.theme import (
    BG_DEEP, BG_PANEL, BG_CARD,
    ACCENT_PURP, ACCENT_LIGHT,
    TEXT_WHITE, TEXT_DIM, WARN_ORANGE,
    GENRE_BG, GENRE_BORDER, GENRE_ACTIVE, GENRE_TXT,
)
from processor.loader import load_json_file, gamedata_to_ui
from processor.filter_sort import filter_and_sort
from scraper.pipeline import BitScorePipeline
from utils.logger import setup_logging

from ui.fonts import build_fonts
from ui.game_card import build_game_card
from ui.sidebar import build_sidebar, refresh_genre_buttons
from ui.scrape_dialog import ScrapeDialog
from ui.detail_popup import DetailPopup
from ui.search_popup import open_search_popup

log = setup_logging(OUTPUT_DIR)


class BitScoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BitScore — Game Ratings")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(bg=BG_DEEP)
        self.resizable(True, True)

        # State
        self.games: list        = []
        self.search_var         = tk.StringVar()
        self.sort_by            = tk.StringVar(value="Rating")
        self.sort_dir           = "desc"
        self.active_genres: set = set()
        self._sort_popup        = None
        self._search_popup      = None
        self._scraping          = False

        self.fonts = build_fonts()
        self._build_ui()

        if LATEST_JSON.exists():
            self._load_file(LATEST_JSON, silent=True)
        else:
            self._show_welcome()

        self.search_var.trace_add("write", self._on_search_change)

    # ── UI Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=BG_DEEP)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._build_main_list(body)
        self._build_sidebar(body)

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_DEEP, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        lf = tk.Frame(hdr, bg=BG_DEEP)
        lf.pack(side="left", padx=20, pady=10)
        tk.Label(lf, text="B",       font=self.fonts["logo"],
                 fg=ACCENT_PURP, bg=BG_DEEP).pack(side="left")
        tk.Label(lf, text="itScore", font=self.fonts["logo"],
                 fg=TEXT_WHITE, bg=BG_DEEP).pack(side="left")

        tk.Button(
            hdr, text="🚀  Scrape Sekarang", font=self.fonts["small"],
            fg=TEXT_WHITE, bg=ACCENT_PURP,
            activebackground=ACCENT_LIGHT, activeforeground=TEXT_WHITE,
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self._open_scrape_dialog,
        ).pack(side="right", padx=16, pady=12)

    def _build_main_list(self, body):
        left = tk.Frame(body, bg=BG_DEEP)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Toolbar
        toolbar = tk.Frame(left, bg=BG_PANEL, height=42)
        toolbar.pack(fill="x", pady=(0, 8))
        toolbar.pack_propagate(False)

        self.sort_dir_btn = tk.Button(
            toolbar, text="↓  Rating", font=self.fonts["sort"],
            fg=TEXT_WHITE, bg=BG_PANEL, activebackground=BG_CARD,
            activeforeground=TEXT_WHITE, relief="flat", cursor="hand2",
            command=self._toggle_sort_dir,
        )
        self.sort_dir_btn.pack(side="left", padx=10, pady=6)

        self.count_lbl = tk.Label(toolbar, text="", font=self.fonts["small"],
                                  fg=TEXT_DIM, bg=BG_PANEL)
        self.count_lbl.pack(side="left", padx=6)

        self.status_lbl = tk.Label(toolbar, text="", font=self.fonts["small"],
                                   fg=WARN_ORANGE, bg=BG_PANEL)
        self.status_lbl.pack(side="left", padx=10)

        tk.Button(
            toolbar, text="Sort by  ▼", font=self.fonts["sort"],
            fg=TEXT_WHITE, bg=BG_PANEL, activebackground=BG_CARD,
            activeforeground=TEXT_WHITE, relief="flat", cursor="hand2",
            command=self._open_sort_popup,
        ).pack(side="right", padx=10, pady=6)

        # Scrollable list
        lc = tk.Frame(left, bg=BG_DEEP)
        lc.pack(fill="both", expand=True)
        self.canvas_list = tk.Canvas(lc, bg=BG_DEEP, highlightthickness=0)
        sb = tk.Scrollbar(lc, orient="vertical", command=self.canvas_list.yview)
        self.canvas_list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas_list.pack(side="left", fill="both", expand=True)

        self.game_frame = tk.Frame(self.canvas_list, bg=BG_DEEP)
        self.canvas_win = self.canvas_list.create_window(
            (0, 0), window=self.game_frame, anchor="nw")
        self.game_frame.bind(
            "<Configure>",
            lambda e: self.canvas_list.configure(
                scrollregion=self.canvas_list.bbox("all")))
        self.canvas_list.bind(
            "<Configure>",
            lambda e: self.canvas_list.itemconfig(self.canvas_win, width=e.width))
        self.canvas_list.bind("<MouseWheel>", self._on_mousewheel)
        self.game_frame.bind("<MouseWheel>",  self._on_mousewheel)

    def _build_sidebar(self, body):
        refs = build_sidebar(
            body, self.fonts,
            self.search_var,
            on_search_focus_in  = self._search_focus_in,
            on_search_focus_out = self._search_focus_out,
            on_search_return    = lambda e: self._render_games(),
            on_search_btn       = self._render_games,
            on_genre_toggle     = self._toggle_genre,
        )
        self.search_entry  = refs["search_entry"]
        self.genre_frame   = refs["genre_frame"]
        self.source_var    = refs["source_var"]
        self.genre_buttons = refs["genre_buttons"]

    # ── Data Loading ──────────────────────────────────────────────────────────

    def _load_file(self, path: Path, silent: bool = False):
        try:
            self.games = load_json_file(path)
        except Exception as e:
            if not silent:
                msgbox.showerror("Error", f"Gagal membaca file:\n{e}")
            return
        self._refresh_genres()
        ts = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        self.source_var.set(
            f"📄 {path.name}\n"
            f"✅ {len(self.games)} games\n"
            f"🕐 {ts}\n"
            f"🌐 RAWG + Steam + CheapShark")
        self._render_games()

    def _refresh_genres(self):
        genres: set = set()
        for g in self.games:
            genres.update(g["genres"])
        self.active_genres.clear()
        self.genre_buttons = refresh_genre_buttons(
            self.genre_frame, self.genre_buttons,
            genres, self.fonts, self._toggle_genre,
        )

    # ── Welcome Screen ────────────────────────────────────────────────────────

    def _show_welcome(self):
        for w in self.game_frame.winfo_children():
            w.destroy()
        msg = tk.Frame(self.game_frame, bg=BG_DEEP)
        msg.pack(pady=80)
        tk.Label(msg, text="🎮", font=tk.font.Font(size=48), bg=BG_DEEP).pack()
        tk.Label(msg, text="Belum ada data game.", font=self.fonts["sub"],
                 fg=TEXT_DIM, bg=BG_DEEP).pack(pady=(8, 4))
        tk.Label(msg,
                 text="Klik  🚀 Scrape Sekarang  untuk mengambil data terbaru.",
                 font=self.fonts["small"], fg=TEXT_DIM, bg=BG_DEEP).pack()
        tk.Button(
            msg, text="🚀  Scrape Sekarang", font=self.fonts["sub"],
            fg=TEXT_WHITE, bg=ACCENT_PURP,
            activebackground=ACCENT_LIGHT, activeforeground=TEXT_WHITE,
            relief="flat", cursor="hand2", padx=16, pady=8,
            command=self._open_scrape_dialog,
        ).pack(pady=16)

    # ── Scraping ──────────────────────────────────────────────────────────────

    def _open_scrape_dialog(self):
        if self._scraping:
            msgbox.showinfo("Info", "Scraping sedang berjalan, harap tunggu...")
            return
        if not REQUESTS_AVAILABLE:
            msgbox.showerror("Error",
                             "Library 'requests' tidak ditemukan!\n"
                             "Install: pip install requests python-dotenv")
            return
        ScrapeDialog(self, self._run_scrape)

    def _run_scrape(self, mode: str, value: str):
        self._scraping = True
        self.status_lbl.configure(text="⏳ Scraping...")
        self.count_lbl.configure(text="")

        def worker():
            try:
                pipeline = BitScorePipeline(rawg_key=RAWG_API_KEY,
                                            output_dir=str(OUTPUT_DIR))

                def on_progress(i, total, name):
                    self.after(0, self.status_lbl.configure,
                               {"text": f"⏳ [{i}/{total}] {name[:30]}..."})

                if mode == "top":
                    count = int(value) if value.isdigit() else 10
                    games = pipeline.scrape_top_games(count=count,
                                                      progress_cb=on_progress)
                else:
                    games = pipeline.scrape_by_query(query=value, limit=20,
                                                     progress_cb=on_progress)

                ui_games = gamedata_to_ui(games)
                self.after(0, self._on_scrape_done, ui_games, len(games))
            except Exception as e:
                self.after(0, self._on_scrape_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scrape_done(self, ui_games: list, count: int):
        self._scraping = False
        self.games     = ui_games
        self.status_lbl.configure(text=f"✅ {count} game berhasil discrape!")
        self.after(4000, lambda: self.status_lbl.configure(text=""))
        self._refresh_genres()
        ts = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.source_var.set(
            f"🌐 Live Scraping\n"
            f"✅ {count} games\n"
            f"🕐 {ts}\n"
            f"RAWG + Steam + CheapShark")
        self._render_games()

    def _on_scrape_error(self, err: str):
        self._scraping = False
        self.status_lbl.configure(text="❌ Scraping gagal!")
        self.after(5000, lambda: self.status_lbl.configure(text=""))
        msgbox.showerror("Scraping Error",
                         f"Terjadi error:\n\n{err}\n\n"
                         "Pastikan RAWG_API_KEY valid dan koneksi internet aktif.")

    # ── Render ────────────────────────────────────────────────────────────────

    def _render_games(self, *_):
        for w in self.game_frame.winfo_children():
            w.destroy()

        filtered = filter_and_sort(
            self.games,
            query         = self.search_var.get(),
            active_genres = self.active_genres,
            sort_by       = self.sort_by.get(),
            direction     = self.sort_dir,
        )
        self.count_lbl.configure(text=f"{len(filtered)} games")

        if not filtered:
            tk.Label(self.game_frame, text="No games found.",
                     font=self.fonts["sub"], fg=TEXT_DIM, bg=BG_DEEP).pack(pady=40)
        else:
            for rank, game in enumerate(filtered, 1):
                build_game_card(
                    self.game_frame, game, rank, self.fonts,
                    on_click = lambda g: DetailPopup(self, g),
                    after_fn = self.after,
                )

    # ── Sort ──────────────────────────────────────────────────────────────────

    def _open_sort_popup(self):
        if self._sort_popup:
            self._close_sort_popup()
            return
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg=BG_PANEL)
        self._sort_popup = popup
        x = self.winfo_x() + self.winfo_width() - 420
        y = self.winfo_y() + 100
        popup.geometry(f"180x90+{x}+{y}")
        for opt in ["Rating", "Name"]:
            tk.Button(
                popup, text=opt, font=self.fonts["sort"],
                fg=TEXT_WHITE, bg=BG_PANEL,
                activebackground=ACCENT_PURP, activeforeground=TEXT_WHITE,
                relief="flat", cursor="hand2", anchor="w", padx=14,
                command=lambda o=opt: self._select_sort(o),
            ).pack(fill="x", ipady=8)
            tk.Frame(popup, bg=BG_PANEL, height=1).pack(fill="x")
        popup.bind("<FocusOut>", lambda e: self._close_sort_popup())
        popup.focus_set()

    def _close_sort_popup(self):
        if self._sort_popup:
            self._sort_popup.destroy()
            self._sort_popup = None

    def _select_sort(self, opt: str):
        self.sort_by.set(opt)
        self._close_sort_popup()
        self._render_games()

    def _toggle_sort_dir(self):
        self.sort_dir = "asc" if self.sort_dir == "desc" else "desc"
        arrow = "↑" if self.sort_dir == "asc" else "↓"
        self.sort_dir_btn.configure(text=f"{arrow}  {self.sort_by.get()}")
        self._render_games()

    # ── Search ────────────────────────────────────────────────────────────────

    def _on_search_change(self, *_):
        q = self.search_var.get().strip().lower()
        if q and q != "search games...":
            self._close_search_popup()
            popup = open_search_popup(
                self, self.search_entry, self.search_var,
                self.games, self.fonts,
                on_select = self._select_search_suggestion,
                after_fn  = self.after,
            )
            self._search_popup = popup
        else:
            self._close_search_popup()
            self._render_games()

    def _select_search_suggestion(self, title: str):
        self.search_var.set(title)
        self._close_search_popup()
        self._render_games()

    def _close_search_popup(self):
        if self._search_popup:
            self._search_popup.destroy()
            self._search_popup = None

    def _search_focus_in(self, e):
        if self.search_var.get() == "Search games...":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg=TEXT_WHITE)

    def _search_focus_out(self, e):
        if not self.search_var.get():
            self.search_entry.insert(0, "Search games...")
            self.search_entry.configure(fg=TEXT_DIM)

    # ── Genre ─────────────────────────────────────────────────────────────────

    def _toggle_genre(self, genre: str):
        if genre in self.active_genres:
            self.active_genres.discard(genre)
            self.genre_buttons[genre].configure(
                bg=GENRE_BG, fg=GENRE_TXT, highlightbackground=GENRE_BORDER)
        else:
            self.active_genres.add(genre)
            self.genre_buttons[genre].configure(
                bg=GENRE_ACTIVE, fg=TEXT_WHITE, highlightbackground=GENRE_ACTIVE)
        self._render_games()

    # ── Misc ──────────────────────────────────────────────────────────────────

    def _on_mousewheel(self, e):
        self.canvas_list.yview_scroll(int(-1 * (e.delta / 120)), "units")
