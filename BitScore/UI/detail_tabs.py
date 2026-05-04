"""
ui/detail_tabs.py
-----------------
Builder untuk tiap tab di dalam DetailPopup:
  - Tab Info & Deskripsi
  - Tab Preview Screenshots
  - Tab PC Requirements
"""

import tkinter as tk
import tkinter.font as tkfont

from config.theme import (
    BG_DEEP, BG_CARD, BORDER_COL, SHOT_W, SHOT_H,
    TEXT_WHITE, TEXT_DIM, TEXT_MUTED, ACCENT_LIGHT,
    REQ_BG,
)
from utils.image_cache import IMAGE_CACHE


def build_info_tab(parent, game: dict, fonts: dict) -> tk.Frame:
    frame = tk.Frame(parent, bg=BG_DEEP)

    info_rows = [
        ("Platforms", "  ·  ".join(game["platforms"]) or "N/A"),
        ("Tags",      "  ·  ".join(game["tags"][:10])),
    ]
    for label, value in info_rows:
        if value:
            row = tk.Frame(frame, bg=BG_DEEP)
            row.pack(fill="x", padx=16, pady=(6, 0))
            tk.Label(row, text=f"{label}:", font=fonts["label"],
                     fg=TEXT_DIM, bg=BG_DEEP, width=9, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=fonts["small"], fg=TEXT_WHITE,
                     bg=BG_DEEP, wraplength=650, justify="left").pack(side="left")

    tk.Frame(frame, bg=BORDER_COL, height=1).pack(fill="x", padx=16, pady=8)

    tk.Label(frame, text="Deskripsi", font=fonts["label"],
             fg=TEXT_DIM, bg=BG_DEEP).pack(anchor="w", padx=16)

    df = tk.Frame(frame, bg=BG_DEEP)
    df.pack(fill="both", expand=True, padx=16, pady=(4, 0))
    ds = tk.Scrollbar(df, orient="vertical")
    dt = tk.Text(df, font=fonts["desc"], fg=TEXT_DIM, bg=BG_DEEP,
                 relief="flat", wrap="word", yscrollcommand=ds.set,
                 highlightthickness=0)
    ds.configure(command=dt.yview)
    ds.pack(side="right", fill="y")
    dt.pack(fill="both", expand=True)
    dt.insert("1.0", game["description"] or "(Tidak ada deskripsi)")
    dt.configure(state="disabled")

    return frame


def build_preview_tab(parent, game: dict, fonts: dict,
                      after_fn, shot_images: list) -> tk.Frame:
    frame       = tk.Frame(parent, bg=BG_DEEP)
    screenshots = game.get("screenshots") or []
    cols        = 3

    if not screenshots:
        tk.Label(frame, text="Tidak ada screenshot tersedia.",
                 font=fonts["small"], fg=TEXT_DIM, bg=BG_DEEP).pack(pady=40)
        return frame

    tk.Label(frame, text=f"Screenshots  ({len(screenshots)} gambar)",
             font=fonts["label"], fg=TEXT_DIM, bg=BG_DEEP).pack(
                 anchor="w", padx=16, pady=(8, 4))

    outer  = tk.Frame(frame, bg=BG_DEEP)
    outer.pack(fill="both", expand=True, padx=12)
    canvas = tk.Canvas(outer, bg=BG_DEEP, highlightthickness=0)
    vsb    = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner  = tk.Frame(canvas, bg=BG_DEEP)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<MouseWheel>",
                lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    for idx, url in enumerate(screenshots):
        row_idx, col_idx = divmod(idx, cols)
        cell = tk.Frame(inner, bg=BG_CARD)
        cell.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")

        shot_canvas = tk.Canvas(cell, width=SHOT_W, height=SHOT_H,
                                bg=BG_CARD, highlightthickness=0)
        shot_canvas.pack()
        shot_canvas.create_text(SHOT_W//2, SHOT_H//2, text="Loading...",
                                font=fonts["small"], fill=TEXT_MUTED)

        def _load_shot(img, c=shot_canvas):
            if img:
                shot_images.append(img)
                c.delete("all")
                c.create_image(0, 0, anchor="nw", image=img)

        IMAGE_CACHE.get(url, size=(SHOT_W, SHOT_H),
                        callback=lambda img, fn=_load_shot: after_fn(0, fn, img))

    for c in range(cols):
        inner.columnconfigure(c, weight=1)

    return frame


def build_requirements_tab(parent, game: dict, fonts: dict) -> tk.Frame:
    frame  = tk.Frame(parent, bg=BG_DEEP)
    pc_min = game.get("pc_minimum") or ""
    pc_rec = game.get("pc_recommended") or ""

    if not pc_min and not pc_rec:
        tk.Label(frame, text="Data PC Requirements tidak tersedia.",
                 font=fonts["small"], fg=TEXT_DIM, bg=BG_DEEP).pack(pady=40)
        return frame

    cols_frame = tk.Frame(frame, bg=BG_DEEP)
    cols_frame.pack(fill="both", expand=True, padx=12, pady=8)

    for title, content in [("💻  Minimum", pc_min), ("⚡  Recommended", pc_rec)]:
        if not content:
            continue
        col = tk.Frame(cols_frame, bg=REQ_BG)
        col.pack(side="left", fill="both", expand=True, padx=6, pady=4)

        tk.Label(col, text=title, font=fonts["label"],
                 fg=ACCENT_LIGHT, bg=REQ_BG, pady=8).pack(anchor="w", padx=10)
        tk.Frame(col, bg=BORDER_COL, height=1).pack(fill="x", padx=8)

        lines = [l.strip() for l in content.split("  ") if l.strip()] or [content]

        txt_frame = tk.Frame(col, bg=REQ_BG)
        txt_frame.pack(fill="both", expand=True, padx=10, pady=8)

        for line in lines:
            if ":" in line:
                parts   = line.split(":", 1)
                key_lbl = parts[0].strip()
                val_lbl = parts[1].strip() if len(parts) > 1 else ""
                row     = tk.Frame(txt_frame, bg=REQ_BG)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"{key_lbl}:", font=fonts["label"],
                         fg=TEXT_DIM, bg=REQ_BG, anchor="w",
                         width=14).pack(side="left")
                tk.Label(row, text=val_lbl, font=fonts["req"],
                         fg=TEXT_WHITE, bg=REQ_BG, anchor="w",
                         wraplength=260, justify="left").pack(side="left", fill="x")
            else:
                tk.Label(txt_frame, text=line, font=fonts["req"],
                         fg=TEXT_WHITE, bg=REQ_BG, anchor="w",
                         wraplength=300, justify="left").pack(anchor="w", pady=1)

    return frame
