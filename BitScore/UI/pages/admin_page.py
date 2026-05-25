"""
ui/pages/admin_page.py
======================
AdminPage: dashboard khusus admin dengan dua tab:
  1. Manajemen User  — tambah, hapus, ganti role/password
  2. Manajemen Konten— statistik game, hapus cache, export JSON
"""

import json
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import tkinter.simpledialog as simpledialog

from config.theme import (
    BG_DEEP, BG_PANEL, BG_CARD, BG_SURFACE2, BG_SURFACE3,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_DIM, ACCENT_BG,
    GREEN, GREEN_BG, GREEN_DIM,
    RED_COL, RED_BG,
    AMBER, AMBER_BG,
    TEAL, TEAL_BG,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    F, FM, divider,
)
from auth.session import SESSION
from store.user_store import USER_STORE
from store.local_store import STORE
from models.user import Role
from config.settings import LATEST_JSON, OUTPUT_DIR


class AdminPage(tk.Frame):
    """
    Frame halaman admin. Di-pack/unpack oleh app.py saat navigasi.
    Memerlukan SESSION.is_admin == True untuk ditampilkan.
    """

    def __init__(self, master, parent_app):
        super().__init__(master, bg=BG_DEEP)
        self.app = parent_app
        self._active_tab = tk.StringVar(value="users")
        self._tab_frames: dict = {}
        self._build()

    # ══════════════════════════════════════════════════════════════════════════
    #  SHELL
    # ══════════════════════════════════════════════════════════════════════════
    def _build(self):
        # Header strip
        tk.Frame(self, bg=RED_COL, height=3).pack(fill="x")
        hdr = tk.Frame(self, bg=BG_PANEL)
        hdr.pack(fill="x")

        left = tk.Frame(hdr, bg=BG_PANEL)
        left.pack(side="left", padx=16, pady=12)
        tk.Button(left, text="←  Back", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self.app._go_back).pack(side="left")
        tk.Label(left, text="  Admin Panel", font=F(14, True), fg=RED_COL, bg=BG_PANEL).pack(side="left")

        # Logged-in user info
        tk.Label(hdr, text=f"🔐  {SESSION.username}", font=F(10),
                 fg=TEXT_DIM, bg=BG_PANEL).pack(side="right", padx=16)

        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")

        # Tab bar
        tab_bar = tk.Frame(self, bg=BG_PANEL)
        tab_bar.pack(fill="x")
        self._tab_btns = {}
        for tid, label in [("users", "  👥  Manajemen User  "),
                            ("content", "  🗂  Manajemen Konten  ")]:
            btn = tk.Button(tab_bar, text=label, font=F(10), fg=TEXT_DIM, bg=BG_PANEL,
                            relief="flat", cursor="hand2", pady=11,
                            command=lambda t=tid: self._switch_tab(t))
            btn.pack(side="left")
            self._tab_btns[tid] = btn
        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")

        # Content area
        body = tk.Frame(self, bg=BG_DEEP)
        body.pack(fill="both", expand=True)

        self._tab_frames["users"]   = self._build_users_tab(body)
        self._tab_frames["content"] = self._build_content_tab(body)

        self._switch_tab("users")

    def _switch_tab(self, tid: str):
        for t, btn in self._tab_btns.items():
            active = (t == tid)
            btn.configure(fg=TEXT_WHITE if active else TEXT_DIM,
                          bg=BG_SURFACE2 if active else BG_PANEL,
                          font=F(10, active))
        for t, frm in self._tab_frames.items():
            frm.pack(fill="both", expand=True) if t == tid else frm.pack_forget()
        self._active_tab.set(tid)
        if tid == "users":
            self._refresh_user_list()
        elif tid == "content":
            self._refresh_content_stats()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — MANAJEMEN USER
    # ══════════════════════════════════════════════════════════════════════════
    def _build_users_tab(self, parent) -> tk.Frame:
        frm = tk.Frame(parent, bg=BG_DEEP)

        # Toolbar
        tb = tk.Frame(frm, bg=BG_PANEL)
        tb.pack(fill="x")
        tk.Frame(tb, bg=BORDER2, height=1).pack(side="bottom", fill="x")
        self._user_count_lbl = tk.Label(tb, text="", font=F(9), fg=TEXT_MUTED, bg=BG_PANEL)
        self._user_count_lbl.pack(side="left", padx=16, pady=10)
        tk.Button(tb, text="+ Tambah User", font=F(10, True), fg=TEXT_WHITE, bg=ACCENT,
                  activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                  padx=14, pady=6, command=self._add_user).pack(side="right", padx=12, pady=8)

        # List area
        list_area = tk.Frame(frm, bg=BG_DEEP)
        list_area.pack(fill="both", expand=True)

        cv = tk.Canvas(list_area, bg=BG_DEEP, highlightthickness=0)
        vsb = ttk.Scrollbar(list_area, orient="vertical", command=cv.yview,
                            style="Dark.Vertical.TScrollbar")
        cv.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)

        self._user_list_frame = tk.Frame(cv, bg=BG_DEEP)
        cw = cv.create_window((0, 0), window=self._user_list_frame, anchor="nw")
        self._user_list_frame.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(cw, width=e.width))
        cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._user_cv = cv

        return frm

    def _refresh_user_list(self):
        for w in self._user_list_frame.winfo_children():
            w.destroy()

        users = USER_STORE.all_users
        self._user_count_lbl.configure(text=f"{len(users)} user terdaftar")

        # Header row
        hdr = tk.Frame(self._user_list_frame, bg=BG_SURFACE3)
        hdr.pack(fill="x", padx=12, pady=(12, 4))
        for text, w in [("Username", 180), ("Role", 100), ("Dibuat", 180), ("Aksi", 240)]:
            tk.Label(hdr, text=text, font=F(9, True), fg=TEXT_MUTED,
                     bg=BG_SURFACE3, width=w // 8, anchor="w").pack(side="left", padx=10, pady=8)

        for u in users:
            is_self = (u.username.lower() == SESSION.username.lower())
            row_bg  = BG_CARD

            outer = tk.Frame(self._user_list_frame, bg=BORDER2)
            outer.pack(fill="x", padx=12, pady=2)
            row = tk.Frame(outer, bg=row_bg)
            row.pack(fill="x", padx=1, pady=1)

            # Username
            uname_f = tk.Frame(row, bg=row_bg, width=190)
            uname_f.pack(side="left", fill="y")
            uname_f.pack_propagate(False)
            tk.Label(uname_f, text=u.username + (" (you)" if is_self else ""),
                     font=F(10, True), fg=TEXT_WHITE, bg=row_bg).pack(side="left", padx=14, pady=14)

            # Role badge
            role_f = tk.Frame(row, bg=row_bg, width=110)
            role_f.pack(side="left", fill="y")
            role_f.pack_propagate(False)
            role_col  = RED_COL if u.is_admin() else TEAL
            role_bg   = RED_BG  if u.is_admin() else TEAL_BG
            badge = tk.Frame(role_f, bg=role_bg, highlightthickness=1, highlightbackground=role_col)
            badge.pack(side="left", padx=8, pady=12)
            tk.Label(badge, text="ADMIN" if u.is_admin() else "USER",
                     font=FM(9, True), fg=role_col, bg=role_bg, padx=8, pady=3).pack()

            # Created at
            ca_f = tk.Frame(row, bg=row_bg, width=190)
            ca_f.pack(side="left", fill="y")
            ca_f.pack_propagate(False)
            created = (u.created_at or "")[:10]
            tk.Label(ca_f, text=created, font=F(9), fg=TEXT_DIM, bg=row_bg).pack(side="left", padx=10, pady=14)

            # Action buttons
            act = tk.Frame(row, bg=row_bg)
            act.pack(side="right", padx=10, pady=10)

            # Toggle role
            if not is_self:
                new_role   = Role.USER if u.is_admin() else Role.ADMIN
                toggle_txt = "→ User" if u.is_admin() else "→ Admin"
                toggle_col = AMBER if u.is_admin() else ACCENT
                tk.Button(act, text=toggle_txt, font=F(9), fg=toggle_col, bg=BG_SURFACE3,
                          relief="flat", cursor="hand2", padx=10, pady=5,
                          command=lambda un=u.username, nr=new_role: self._toggle_role(un, nr)
                          ).pack(side="left", padx=(0, 6))

            # Change password
            tk.Button(act, text="Ganti PW", font=F(9), fg=TEXT_DIM, bg=BG_SURFACE3,
                      relief="flat", cursor="hand2", padx=10, pady=5,
                      command=lambda un=u.username: self._change_password(un)).pack(side="left", padx=(0, 6))

            # Delete
            if not is_self:
                tk.Button(act, text="Hapus", font=F(9), fg=RED_COL, bg=RED_BG,
                          relief="flat", cursor="hand2", padx=10, pady=5,
                          command=lambda un=u.username: self._delete_user(un)).pack(side="left")

    def _add_user(self):
        dlg = _UserDialog(self, title="Tambah User Baru")
        self.wait_window(dlg)
        if dlg.result:
            username, password, role = dlg.result
            ok = USER_STORE.add(username, password, role)
            if ok:
                self._refresh_user_list()
            else:
                msgbox.showerror("Error", f"Username '{username}' sudah dipakai.", parent=self)

    def _toggle_role(self, username: str, new_role: Role):
        label = "Admin" if new_role == Role.ADMIN else "User"
        if not msgbox.askyesno("Konfirmasi", f"Ubah role '{username}' menjadi {label}?", parent=self):
            return
        ok = USER_STORE.change_role(username, new_role)
        if not ok:
            msgbox.showerror("Error", "Tidak bisa mengubah role. Minimal harus ada 1 admin.", parent=self)
        self._refresh_user_list()

    def _change_password(self, username: str):
        new_pw = simpledialog.askstring(
            "Ganti Password",
            f"Password baru untuk '{username}':",
            parent=self, show="●"
        )
        if not new_pw:
            return
        if len(new_pw) < 6:
            msgbox.showerror("Error", "Password minimal 6 karakter.", parent=self)
            return
        USER_STORE.change_password(username, new_pw)
        msgbox.showinfo("Sukses", f"Password '{username}' berhasil diubah.", parent=self)

    def _delete_user(self, username: str):
        if not msgbox.askyesno("Hapus User", f"Yakin hapus user '{username}'?\nAksi ini tidak bisa dibatalkan.", parent=self):
            return
        ok = USER_STORE.delete(username)
        if not ok:
            msgbox.showerror("Error", "Tidak bisa menghapus. Minimal harus ada 1 admin.", parent=self)
        self._refresh_user_list()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — MANAJEMEN KONTEN
    # ══════════════════════════════════════════════════════════════════════════
    def _build_content_tab(self, parent) -> tk.Frame:
        frm = tk.Frame(parent, bg=BG_DEEP)

        body = tk.Frame(frm, bg=BG_DEEP)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        # Stat cards row
        stat_row = tk.Frame(body, bg=BG_DEEP)
        stat_row.pack(fill="x", pady=(0, 20))
        self._stat_cards: dict = {}
        for key, label, color in [
            ("games",    "Total Game",    ACCENT_LIGHT),
            ("wishlist", "Di Wishlist",   AMBER),
            ("reviews",  "Review Ditulis", GREEN),
            ("cache",    "Cache Gambar",  TEAL),
        ]:
            card = tk.Frame(stat_row, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER2)
            card.pack(side="left", padx=(0, 12), pady=4, fill="y")
            num_lbl = tk.Label(card, text="—", font=FM(24, True), fg=color, bg=BG_CARD, padx=24, pady=12)
            num_lbl.pack()
            tk.Label(card, text=label, font=F(9), fg=TEXT_DIM, bg=BG_CARD, padx=24).pack(pady=(0, 10))
            self._stat_cards[key] = num_lbl

        divider(body, pady=(0, 14))

        # Action buttons
        tk.Label(body, text="AKSI KONTEN", font=F(9, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 10))
        actions = tk.Frame(body, bg=BG_DEEP)
        actions.pack(anchor="w")

        action_list = [
            ("Export Data Game (JSON)",  ACCENT_LIGHT, ACCENT_BG, self._export_json),
            ("Hapus Cache Gambar",       AMBER,        AMBER_BG,  self._clear_img_cache),
            ("Hapus Semua Review",       RED_COL,      RED_BG,    self._clear_reviews),
            ("Hapus Semua Wishlist",     RED_COL,      RED_BG,    self._clear_wishlist),
        ]
        for txt, fg, bg, cmd in action_list:
            tk.Button(actions, text=txt, font=F(10), fg=fg, bg=bg,
                      relief="flat", cursor="hand2", padx=16, pady=9,
                      command=cmd).pack(side="left", padx=(0, 10))

        divider(body, pady=(20, 14))

        # Log area
        tk.Label(body, text="LOG AKTIVITAS ADMIN", font=F(9, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 6))
        log_f = tk.Frame(body, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER2)
        log_f.pack(fill="both", expand=True)
        vsb2 = ttk.Scrollbar(log_f, orient="vertical", style="Dark.Vertical.TScrollbar")
        self._log_txt = tk.Text(log_f, font=FM(9), fg=GREEN, bg=BG_CARD, relief="flat",
                                wrap="word", yscrollcommand=vsb2.set, highlightthickness=0,
                                padx=12, pady=8, insertbackground=TEXT_WHITE, state="disabled")
        vsb2.configure(command=self._log_txt.yview)
        vsb2.pack(side="right", fill="y")
        self._log_txt.pack(fill="both", expand=True)

        return frm

    def _refresh_content_stats(self):
        from utils.img_cache import IMG_CACHE_DIR
        game_count = len(self.app.games) if hasattr(self.app, "games") else 0
        wl_count   = len(STORE.wishlist)
        rv_count   = len(STORE.reviews)
        try:
            cache_count = len(list(IMG_CACHE_DIR.glob("*.png")))
        except Exception:
            cache_count = 0
        self._stat_cards["games"].configure(text=str(game_count))
        self._stat_cards["wishlist"].configure(text=str(wl_count))
        self._stat_cards["reviews"].configure(text=str(rv_count))
        self._stat_cards["cache"].configure(text=str(cache_count))

    def _log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_txt.configure(state="normal")
        self._log_txt.insert("end", f"[{ts}] {msg}\n")
        self._log_txt.see("end")
        self._log_txt.configure(state="disabled")

    def _export_json(self):
        if not LATEST_JSON.exists():
            msgbox.showinfo("Info", "Belum ada data game. Lakukan scraping terlebih dahulu.", parent=self)
            return
        from datetime import datetime
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = OUTPUT_DIR / f"export_{ts}.json"
        dest.write_bytes(LATEST_JSON.read_bytes())
        self._log(f"Export berhasil → {dest.name}")
        msgbox.showinfo("Export Sukses", f"Data disimpan ke:\n{dest}", parent=self)

    def _clear_img_cache(self):
        if not msgbox.askyesno("Hapus Cache", "Hapus semua cache gambar?\n(Gambar akan diunduh ulang saat diperlukan)", parent=self):
            return
        from utils.img_cache import IMG
        IMG.clear_disk_cache()
        self._log("Cache gambar dihapus.")
        self._refresh_content_stats()
        msgbox.showinfo("Sukses", "Cache gambar berhasil dihapus.", parent=self)

    def _clear_reviews(self):
        if not msgbox.askyesno("Hapus Review", "Hapus SEMUA review?\nAksi ini tidak bisa dibatalkan.", parent=self):
            return
        from config.settings import REVIEWS_JSON
        if REVIEWS_JSON.exists():
            REVIEWS_JSON.write_text("{}",  encoding="utf-8")
        STORE._rv.clear()
        self._log("Semua review dihapus.")
        self._refresh_content_stats()

    def _clear_wishlist(self):
        if not msgbox.askyesno("Hapus Wishlist", "Hapus SEMUA wishlist?\nAksi ini tidak bisa dibatalkan.", parent=self):
            return
        from config.settings import WISHLIST_JSON
        if WISHLIST_JSON.exists():
            WISHLIST_JSON.write_text("[]", encoding="utf-8")
        STORE._wl.clear()
        self._log("Semua wishlist dihapus.")
        self._refresh_content_stats()


# ══════════════════════════════════════════════════════════════════════════════
#  DIALOG: Tambah User
# ══════════════════════════════════════════════════════════════════════════════
class _UserDialog(tk.Toplevel):
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=BG_PANEL)
        self.geometry("380x360")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")
        wrap = tk.Frame(self, bg=BG_PANEL)
        wrap.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(wrap, text="Tambah User Baru", font=F(13, True), fg=TEXT_WHITE, bg=BG_PANEL).pack(anchor="w", pady=(0, 16))

        for label, var_name, show in [
            ("USERNAME", "_uv", ""),
            ("PASSWORD", "_pv", "●"),
        ]:
            tk.Label(wrap, text=label, font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
            ef = tk.Frame(wrap, bg=BG_SURFACE3, highlightthickness=1, highlightbackground=BORDER2)
            ef.pack(fill="x", pady=(0, 12))
            var = tk.StringVar()
            setattr(self, var_name, var)
            tk.Entry(ef, textvariable=var, show=show, font=F(10), fg=TEXT_WHITE, bg=BG_SURFACE3,
                     insertbackground=TEXT_WHITE, relief="flat", highlightthickness=0).pack(fill="x", padx=8, ipady=7)

        tk.Label(wrap, text="ROLE", font=F(8, True), fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))
        self._rv = tk.StringVar(value="user")
        rf = tk.Frame(wrap, bg=BG_PANEL)
        rf.pack(anchor="w", pady=(0, 16))
        for txt, val in [("User", "user"), ("Admin", "admin")]:
            tk.Radiobutton(rf, text=txt, variable=self._rv, value=val, font=F(10),
                           fg=TEXT_WHITE, bg=BG_PANEL, selectcolor=ACCENT,
                           activebackground=BG_PANEL).pack(side="left", padx=(0, 14))

        btn_row = tk.Frame(wrap, bg=BG_PANEL)
        btn_row.pack()
        tk.Button(btn_row, text="Batal", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                  relief="flat", cursor="hand2", padx=18, pady=8,
                  command=self.destroy).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="Simpan", font=F(10, True), fg=TEXT_WHITE, bg=ACCENT,
                  activebackground=ACCENT_LIGHT, relief="flat", cursor="hand2",
                  padx=18, pady=8, command=self._save).pack(side="left")

    def _save(self):
        u = self._uv.get().strip()
        p = self._pv.get().strip()
        r = Role(self._rv.get())
        if len(u) < 3:
            msgbox.showerror("Error", "Username minimal 3 karakter.", parent=self)
            return
        if len(p) < 6:
            msgbox.showerror("Error", "Password minimal 6 karakter.", parent=self)
            return
        self.result = (u, p, r)
        self.destroy()
