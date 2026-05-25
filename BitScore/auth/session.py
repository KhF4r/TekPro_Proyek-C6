"""
auth/session.py
===============
SESSION — singleton yang menyimpan state login aktif.

Dipakai oleh semua halaman untuk tahu:
  - Siapa yang sedang login  : SESSION.current_user
  - Apakah sudah login       : SESSION.is_logged_in
  - Apakah admin             : SESSION.is_admin
"""

from typing import Optional
from models.user import User


class Session:
    def __init__(self):
        self._user: Optional[User] = None

    def login(self, user: User):
        """Set user aktif."""
        self._user = user

    def logout(self):
        """Hapus user aktif."""
        self._user = None

    @property
    def current_user(self) -> Optional[User]:
        return self._user

    @property
    def is_logged_in(self) -> bool:
        return self._user is not None

    @property
    def is_admin(self) -> bool:
        return self._user is not None and self._user.is_admin()

    @property
    def username(self) -> str:
        return self._user.username if self._user else ""


# Singleton — import SESSION dari mana saja
SESSION = Session()
