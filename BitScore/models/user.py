"""
models/user.py
==============
Dataclass User dan enum Role.
Dipakai oleh auth/, store/user_store.py, dan guard.py.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class Role(Enum):
    GUEST = "guest"
    USER  = "user"
    ADMIN = "admin"


@dataclass
class User:
    username:   str
    password:   str          # disimpan sebagai plain-text (cukup untuk MVP desktop)
    role:       Role         = Role.USER
    created_at: str          = field(default_factory=lambda: datetime.now().isoformat())

    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    def is_guest(self) -> bool:
        return self.role == Role.GUEST

    def to_dict(self) -> dict:
        return {
            "username":   self.username,
            "password":   self.password,
            "role":       self.role.value,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "User":
        return User(
            username=d["username"],
            password=d["password"],
            role=Role(d.get("role", "user")),
            created_at=d.get("created_at", ""),
        )