"""
auth/guard.py
=============
Guard: fungsi penjaga akses halaman berdasar role.

Cara pakai di app.py:
    if not guard_login(self): return
    if not guard_admin(self): return
"""

import tkinter.messagebox as msgbox
from auth.session import SESSION


def guard_login(parent=None) -> bool:
    """
    Return True jika user sudah login.
    Tampilkan pesan jika belum.
    """
    if SESSION.is_logged_in:
        return True
    msgbox.showwarning(
        "Login Required",
        "Kamu harus login terlebih dahulu.",
        parent=parent,
    )
    return False


def guard_admin(parent=None) -> bool:
    """
    Return True jika user adalah admin.
    Tampilkan pesan jika bukan admin.
    """
    if not SESSION.is_logged_in:
        msgbox.showwarning("Login Required", "Kamu harus login terlebih dahulu.", parent=parent)
        return False
    if SESSION.is_admin:
        return True
    msgbox.showerror(
        "Access Denied",
        "Halaman ini hanya bisa diakses oleh Admin.",
        parent=parent,
    )
    return False


def require_login(fn):
    """
    Dekorator: wrap fungsi dengan guard_login.
    Pakai untuk method di class App.

    Contoh:
        @require_login
        def _open_wishlist(self):
            ...
    """
    def wrapper(self, *args, **kwargs):
        if guard_login(self):
            return fn(self, *args, **kwargs)
    return wrapper


def require_admin(fn):
    """
    Dekorator: wrap fungsi dengan guard_admin.

    Contoh:
        @require_admin
        def _open_admin_panel(self):
            ...
    """
    def wrapper(self, *args, **kwargs):
        if guard_admin(self):
            return fn(self, *args, **kwargs)
    return wrapper
