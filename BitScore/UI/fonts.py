"""
ui/fonts.py
-----------
Builder untuk semua tkfont.Font yang dipakai di seluruh UI BitScore.
Dipanggil sekali dari BitScoreApp dan hasilnya disimpan sebagai atribut.
"""

import tkinter.font as tkfont


def build_fonts() -> dict:
    """
    Kembalikan dict berisi semua font object yang dibutuhkan UI.
    Harus dipanggil setelah tk.Tk() sudah dibuat.
    """
    return {
        "logo"   : tkfont.Font(family="Georgia", size=24, weight="bold", slant="italic"),
        "title"  : tkfont.Font(family="Georgia", size=14, weight="bold"),
        "sub"    : tkfont.Font(family="Georgia", size=11),
        "badge"  : tkfont.Font(family="Georgia", size=16, weight="bold"),
        "genre"  : tkfont.Font(family="Georgia", size=9,  weight="bold"),
        "rating" : tkfont.Font(family="Georgia", size=12, weight="bold"),
        "sort"   : tkfont.Font(family="Georgia", size=11),
        "section": tkfont.Font(family="Georgia", size=11, weight="bold"),
        "search" : tkfont.Font(family="Georgia", size=10),
        "small"  : tkfont.Font(family="Georgia", size=9),
        "dev"    : tkfont.Font(family="Georgia", size=9,  slant="italic"),
        "meta"   : tkfont.Font(family="Georgia", size=10, weight="bold"),
        "price"  : tkfont.Font(family="Georgia", size=9,  weight="bold"),
        # Detail popup specific
        "big"    : tkfont.Font(family="Georgia", size=16, weight="bold"),
        "desc"   : tkfont.Font(family="Georgia", size=10),
        "req"    : tkfont.Font(family="Courier", size=9),
        "label"  : tkfont.Font(family="Georgia", size=9,  weight="bold"),
        "tab"    : tkfont.Font(family="Georgia", size=10, weight="bold"),
    }
