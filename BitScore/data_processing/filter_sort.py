"""
processor/filter_sort.py
------------------------
Logika filtering (genre, search query) dan sorting (rating/name, asc/desc).
"""


def filter_games(games: list, query: str = "", active_genres: set = None) -> list:
    """
    Filter list game berdasarkan search query dan genre aktif.

    Parameters
    ----------
    games        : list game dalam format UI dict
    query        : string pencarian (case-insensitive, match di title)
    active_genres: set nama genre yang sedang aktif; None = tanpa filter
    """
    q = query.strip().lower()
    if q in ("", "search games..."):
        q = ""

    result = list(games)

    if active_genres:
        result = [g for g in result
                  if any(genre in g["genres"] for genre in active_genres)]

    if q:
        result = [g for g in result if q in g["title"].lower()]

    return result


def sort_games(games: list, sort_by: str = "Rating",
               direction: str = "desc") -> list:
    """
    Urutkan list game.

    Parameters
    ----------
    sort_by   : "Rating" atau "Name"
    direction : "asc" atau "desc"
    """
    key     = "rating" if sort_by == "Rating" else "title"
    reverse = (direction == "desc")
    return sorted(games, key=lambda g: g[key], reverse=reverse)


def filter_and_sort(games: list, query: str = "",
                    active_genres: set = None,
                    sort_by: str = "Rating",
                    direction: str = "desc") -> list:
    """Gabungan filter + sort dalam satu panggilan."""
    filtered = filter_games(games, query, active_genres)
    return sort_games(filtered, sort_by, direction)
