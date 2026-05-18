"""
auth/login_page.py
==================
LoginPage: halaman login yang ditampilkan sebelum app utama.
Menangani login dan registrasi akun baru (role USER).

Dipanggil dari main.py sebelum BitScoreApp dibuka.
"""

import tkinter as tk
import tkinter.messagebox as msgbox
import tkinter.font as tkfont

from config.theme import (
    BG_DEEP, BG_PANEL, BG_CARD, BG_SURFACE2, BG_SURFACE3,
    BORDER2, ACCENT, ACCENT_LIGHT, ACCENT_DIM, ACCENT_BG,
    GREEN, GREEN_BG, GREEN_DIM,
    RED_COL, RED_BG,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED,
    F, divider,
)
from auth.session import SESSION
from store.user_store import USER_STORE
from models.user import Role


class LoginPage(tk.Tk):
    """
    Window login mandiri.
    Setelah login berhasil, window ini destroy() dan
    BitScoreApp dibuat di main.py.
    """

    def __init__(self):
        super().__init__()
        self.title("BitScore — Login")
        self.geometry("440x640")
        self.resizable(False, False)
        self.configure(bg=BG_DEEP)
        self._logged_in = False
        self._mode      = tk.StringVar(value="login")   # "login" | "register"
        self._build()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 440, 640
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    @property
    def success(self) -> bool:
        return self._logged_in

    # ── Build layout ──────────────────────────────────────────────────────────
    def _build(self):
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

        wrap = tk.Frame(self, bg=BG_DEEP)
        wrap.pack(fill="both", expand=True, padx=40, pady=30)

        # Logo
        logo_f = tk.Frame(wrap, bg=BG_DEEP)
        logo_f.pack(pady=(10, 4))
        tk.Label(logo_f, text="B", font=F(32, True), fg=ACCENT_LIGHT, bg=BG_DEEP).pack(side="left")
        tk.Label(logo_f, text="itScore", font=F(32, True), fg=TEXT_WHITE, bg=BG_DEEP).pack(side="left")
        tk.Label(wrap, text="Game Rating Platform", font=F(10), fg=TEXT_MUTED, bg=BG_DEEP).pack()

        divider(wrap, pady=18)

        # Tab switch
        tab_f = tk.Frame(wrap, bg=BG_SURFACE3, highlightthickness=1, highlightbackground=BORDER2)
        tab_f.pack(fill="x", pady=(0, 20))
        self._tab_login = tk.Button(tab_f, text="Login", font=F(10), fg=TEXT_WHITE, bg=ACCENT,
                                    relief="flat", cursor="hand2", padx=0, pady=8,
                                    command=lambda: self._switch("login"))
        self._tab_login.pack(side="left", fill="x", expand=True)
        self._tab_reg   = tk.Button(tab_f, text="Daftar", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                                    relief="flat", cursor="hand2", padx=0, pady=8,
                                    command=lambda: self._switch("register"))
        self._tab_reg.pack(side="left", fill="x", expand=True)

        # Form fields
        self._form = tk.Frame(wrap, bg=BG_DEEP)
        self._form.pack(fill="x")
        self._build_form()

        # Status label
        self._status = tk.Label(wrap, text="", font=F(9), fg=RED_COL,
                                bg=BG_DEEP, wraplength=340, justify="center")
        self._status.pack(pady=(8, 0))

        # Submit button
        self._submit_btn = tk.Button(wrap, text="Masuk", font=F(12, True), fg=TEXT_WHITE,
                                     bg=ACCENT, activebackground=ACCENT_LIGHT,
                                     relief="flat", cursor="hand2", pady=12,
                                     command=self._submit)
        self._submit_btn.pack(fill="x", pady=(14, 0))

        # Tombol Guest — pemisah
        tk.Label(wrap, text="— atau —", font=F(9), fg=TEXT_MUTED, bg=BG_DEEP).pack(pady=(10, 0))
        tk.Button(wrap, text="👤  Lanjut sebagai Guest", font=F(10), fg=TEXT_DIM,
                  bg=BG_SURFACE3, activebackground=BG_SURFACE2,
                  relief="flat", cursor="hand2", pady=9,
                  command=self._do_guest).pack(fill="x", pady=(6, 0))

        # Hint
        self._hint = tk.Label(wrap, font=F(9), fg=TEXT_MUTED, bg=BG_DEEP)
        self._hint.pack(pady=(12, 0))
        self._update_hint()

        self.bind("<Return>", lambda e: self._submit())

    def _build_form(self):
        for w in self._form.winfo_children():
            w.destroy()

        # Username
        tk.Label(self._form, text="USERNAME", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 4))
        uf = tk.Frame(self._form, bg=BG_SURFACE3, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=ACCENT)
        uf.pack(fill="x", pady=(0, 14))
        self._user_var = tk.StringVar()
        tk.Entry(uf, textvariable=self._user_var, font=F(11), fg=TEXT_WHITE, bg=BG_SURFACE3,
                 insertbackground=TEXT_WHITE, relief="flat", highlightthickness=0).pack(
            fill="x", padx=10, ipady=8)

        # Password
        tk.Label(self._form, text="PASSWORD", font=F(8, True), fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(0, 4))
        pf = tk.Frame(self._form, bg=BG_SURFACE3, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=ACCENT)
        pf.pack(fill="x", pady=(0, 4))
        self._pass_var  = tk.StringVar()
        self._pass_show = tk.BooleanVar(value=False)
        pe = tk.Entry(pf, textvariable=self._pass_var, show="●", font=F(11),
                      fg=TEXT_WHITE, bg=BG_SURFACE3, insertbackground=TEXT_WHITE,
                      relief="flat", highlightthickness=0)
        pe.pack(side="left", fill="x", expand=True, padx=10, ipady=8)
        self._pass_entry = pe

        def _toggle_show():
            self._pass_show.set(not self._pass_show.get())
            pe.configure(show="" if self._pass_show.get() else "●")
            eye_btn.configure(text="🙈" if self._pass_show.get() else "👁")

        eye_btn = tk.Button(pf, text="👁", font=F(10), fg=TEXT_DIM, bg=BG_SURFACE3,
                            relief="flat", cursor="hand2", padx=8,
                            command=_toggle_show, activebackground=BG_SURFACE3)
        eye_btn.pack(side="right")

        # Confirm password (hanya untuk register)
        if self._mode.get() == "register":
            tk.Label(self._form, text="KONFIRMASI PASSWORD", font=F(8, True),
                     fg=TEXT_MUTED, bg=BG_DEEP).pack(anchor="w", pady=(10, 4))
            cf = tk.Frame(self._form, bg=BG_SURFACE3, highlightthickness=1,
                          highlightbackground=BORDER2, highlightcolor=ACCENT)
            cf.pack(fill="x")
            self._conf_var = tk.StringVar()
            tk.Entry(cf, textvariable=self._conf_var, show="●", font=F(11),
                     fg=TEXT_WHITE, bg=BG_SURFACE3, insertbackground=TEXT_WHITE,
                     relief="flat", highlightthickness=0).pack(fill="x", padx=10, ipady=8)
        else:
            self._conf_var = tk.StringVar()

    def _switch(self, mode: str):
        self._mode.set(mode)
        self._status.configure(text="")
        if mode == "login":
            self._tab_login.configure(fg=TEXT_WHITE, bg=ACCENT)
            self._tab_reg.configure(fg=TEXT_DIM, bg=BG_SURFACE3)
            self._submit_btn.configure(text="Masuk")
        else:
            self._tab_reg.configure(fg=TEXT_WHITE, bg=ACCENT)
            self._tab_login.configure(fg=TEXT_DIM, bg=BG_SURFACE3)
            self._submit_btn.configure(text="Daftar Sekarang")
        self._build_form()
        self._update_hint()

    def _update_hint(self):
        if self._mode.get() == "login":
            self._hint.configure(
                text="Demo: admin / admin123   |   user / user123")
        else:
            self._hint.configure(text="Akun baru otomatis mendapat role User.")

    def _submit(self):
        username = self._user_var.get().strip()
        password = self._pass_var.get().strip()
        self._status.configure(text="", fg=RED_COL)

        if not username or not password:
            self._status.configure(text="Username dan password tidak boleh kosong.")
            return

        if self._mode.get() == "login":
            self._do_login(username, password)
        else:
            self._do_register(username, password)

    def _do_login(self, username: str, password: str):
        user = USER_STORE.authenticate(username, password)
        if not user:
            self._status.configure(text="Username atau password salah.")
            return
        SESSION.login(user)
        self._logged_in = True
        self.destroy()

    def _do_register(self, username: str, password: str):
        confirm = self._conf_var.get().strip()
        if password != confirm:
            self._status.configure(text="Password dan konfirmasi tidak cocok.")
            return
        if len(password) < 6:
            self._status.configure(text="Password minimal 6 karakter.")
            return
        if len(username) < 3:
            self._status.configure(text="Username minimal 3 karakter.")
            return
        ok = USER_STORE.add(username, password, Role.USER)
        if not ok:
            self._status.configure(text=f"Username '{username}' sudah dipakai.")
            return
        self._status.configure(text="Akun berhasil dibuat! Silakan login.", fg=GREEN)
        self._switch("login")
        self._user_var.set(username)

    def _do_guest(self):
        """Login sebagai guest — tidak perlu username/password."""
        from models.user import User
        guest_user = User(username="Guest", password="", role=Role.GUEST)
        SESSION.login(guest_user)
        self._logged_in = True
        self.destroy()