"""
store/user_store.py
===================
UserStore: simpan dan load daftar user dari JSON lokal.
Sudah menyertakan akun default (admin + 1 user demo) agar
aplikasi langsung bisa dicoba tanpa setup tambahan.
"""

import json
from pathlib import Path
from models.user import User, Role
from config.settings import OUTPUT_DIR

USERS_JSON = OUTPUT_DIR / "users.json"

# Akun bawaan — muncul saat users.json belum ada
_DEFAULT_USERS: list[dict] = [
    {"username": "admin",   "password": "admin123",  "role": "admin"},
    {"username": "user",    "password": "user123",   "role": "user"},
]


class UserStore:
    def __init__(self):
        self._users: dict[str, User] = {}   # key = username (lowercase)
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self):
        if USERS_JSON.exists():
            try:
                raw = json.loads(USERS_JSON.read_text(encoding="utf-8"))
                self._users = {d["username"].lower(): User.from_dict(d) for d in raw}
                return
            except Exception:
                pass
        # Buat dari default jika file belum ada / rusak
        self._users = {d["username"]: User.from_dict(d) for d in _DEFAULT_USERS}
        self._save()

    def _save(self):
        data = [u.to_dict() for u in self._users.values()]
        USERS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def get(self, username: str):
        """Return User atau None."""
        return self._users.get(username.lower())

    def authenticate(self, username: str, password: str):
        """Return User jika login valid, None jika tidak."""
        u = self.get(username)
        if u and u.password == password:
            return u
        return None

    def add(self, username: str, password: str, role: Role = Role.USER) -> bool:
        """Tambah user baru. Return False jika username sudah ada."""
        if username.lower() in self._users:
            return False
        self._users[username.lower()] = User(username=username, password=password, role=role)
        self._save()
        return True

    def delete(self, username: str) -> bool:
        """Hapus user. Return False jika tidak ditemukan atau target adalah satu-satunya admin."""
        key = username.lower()
        if key not in self._users:
            return False
        # Jangan hapus jika itu satu-satunya admin
        if self._users[key].is_admin():
            admins = [u for u in self._users.values() if u.is_admin()]
            if len(admins) <= 1:
                return False
        del self._users[key]
        self._save()
        return True

    def change_password(self, username: str, new_password: str) -> bool:
        u = self.get(username)
        if not u:
            return False
        u.password = new_password
        self._save()
        return True

    def change_role(self, username: str, new_role: Role) -> bool:
        u = self.get(username)
        if not u:
            return False
        # Jangan downgrade satu-satunya admin
        if u.is_admin() and new_role != Role.ADMIN:
            admins = [x for x in self._users.values() if x.is_admin()]
            if len(admins) <= 1:
                return False
        u.role = new_role
        self._save()
        return True

    @property
    def all_users(self) -> list[User]:
        return list(self._users.values())

    @property
    def user_count(self) -> int:
        return len(self._users)


# Singleton
USER_STORE = UserStore()
