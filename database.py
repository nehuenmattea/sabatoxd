"""
database.py
Capa de acceso a datos para Sábatoxd.
Usa sqlite3 puro (sin ORM) para mantener la app simple y sin dependencias extra.
"""

import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estanteria.db")

# Paleta de colores básicos para las "libretas" (listas)
LIST_COLORS = [
    {"name": "rojo", "hex": "#C1443B"},
    {"name": "naranja", "hex": "#D2793A"},
    {"name": "amarillo", "hex": "#D9B84A"},
    {"name": "verde", "hex": "#4E8F63"},
    {"name": "azul", "hex": "#3D6E9E"},
    {"name": "morado", "hex": "#6E4E8E"},
    {"name": "rosa", "hex": "#C15C86"},
    {"name": "gris", "hex": "#707885"},
]
COLOR_HEX_MAP = {c["name"]: c["hex"] for c in LIST_COLORS}

# Géneros precargados (se insertan solo la primera vez que se crea la base)
DEFAULT_GENRES = [
    "Poesía", "Terror", "Ciencia ficción", "Fantasía", "Romance",
    "Misterio", "Aventura", "Biografía", "Historia", "Ensayo",
    "Infantil", "Juvenil", "Clásico", "Drama", "Humor", "Autoayuda", "No ficción",
]

# Máximo de géneros por libro
MAX_GENRES_PER_BOOK = 5

# Opciones de calificación (con medias estrellas) para el filtro
RATING_OPTIONS = [5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5]

# Columnas válidas para ordenar (whitelist para evitar inyección SQL)
SORT_COLUMNS = {
    "title": "title COLLATE NOCASE",
    "author": "author COLLATE NOCASE",
    "year": "year",
    "pages": "pages",
    "rating": "rating",
    "date_read": "date_read",
    "added": "id",
}


def get_db():
    """Devuelve la conexión SQLite asociada al contexto de la request actual."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_column(conn, table, column, coltype):
    """Agrega una columna a una tabla existente si todavía no existe.
    Permite actualizar bases de datos creadas con una versión anterior
    de la app sin perder los datos ya cargados."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def init_db():
    """Crea las tablas si no existen y aplica migraciones livianas.
    Se puede llamar de forma segura muchas veces."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            year INTEGER,
            pages INTEGER,
            date_read TEXT,
            rating REAL DEFAULT 0,
            cover_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT 'azul',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS list_books (
            list_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            added_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (list_id, book_id),
            FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE
        );

        CREATE TABLE IF NOT EXISTS book_genres (
            book_id INTEGER NOT NULL,
            genre_id INTEGER NOT NULL,
            PRIMARY KEY (book_id, genre_id),
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
        );
        """
    )

    # Migraciones para bases de datos creadas con versiones anteriores
    _ensure_column(conn, "lists", "background_path", "TEXT")
    _ensure_column(conn, "lists", "description", "TEXT")

    # Sembrar géneros por defecto solo si la tabla está vacía
    count = conn.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT OR IGNORE INTO genres (name) VALUES (?)",
            [(g,) for g in DEFAULT_GENRES],
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# LIBROS
# ---------------------------------------------------------------------------

def create_book(title, author, year, pages, date_read, rating, cover_path):
    db = get_db()
    cur = db.execute(
        """INSERT INTO books (title, author, year, pages, date_read, rating, cover_path)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, author, year, pages, date_read, rating, cover_path),
    )
    db.commit()
    return cur.lastrowid


def update_book(book_id, title, author, year, pages, date_read, rating, cover_path=None, keep_cover=True):
    db = get_db()
    if keep_cover:
        db.execute(
            """UPDATE books SET title=?, author=?, year=?, pages=?, date_read=?, rating=?
               WHERE id=?""",
            (title, author, year, pages, date_read, rating, book_id),
        )
    else:
        db.execute(
            """UPDATE books SET title=?, author=?, year=?, pages=?, date_read=?, rating=?, cover_path=?
               WHERE id=?""",
            (title, author, year, pages, date_read, rating, cover_path, book_id),
        )
    db.commit()


def delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()


def get_book(book_id):
    db = get_db()
    return db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()


def get_all_books(sort="added", order="desc", rating_filter="", search="", genre_filter=""):
    db = get_db()
    col = SORT_COLUMNS.get(sort, "id")
    order = "ASC" if order == "asc" else "DESC"

    query = "SELECT books.* FROM books WHERE 1=1"
    params = []

    if genre_filter:
        query += """ AND books.id IN (
            SELECT book_id FROM book_genres WHERE genre_id = ?
        )"""
        params.append(int(genre_filter))

    if rating_filter == "unrated":
        query += " AND (books.rating IS NULL OR books.rating = 0)"
    elif rating_filter:
        try:
            params.append(float(rating_filter))
            query += " AND books.rating = ?"
        except ValueError:
            pass

    if search:
        query += " AND (books.title LIKE ? OR books.author LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])

    query += f" ORDER BY {col} {order}"
    return db.execute(query, params).fetchall()


def get_lists_for_book(book_id):
    db = get_db()
    return db.execute(
        """SELECT lists.* FROM lists
           JOIN list_books ON lists.id = list_books.list_id
           WHERE list_books.book_id = ?
           ORDER BY lists.name COLLATE NOCASE""",
        (book_id,),
    ).fetchall()


def get_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    read = db.execute("SELECT COUNT(*) FROM books WHERE date_read IS NOT NULL AND date_read != ''").fetchone()[0]
    avg_rating = db.execute("SELECT AVG(rating) FROM books WHERE rating > 0").fetchone()[0]
    total_lists = db.execute("SELECT COUNT(*) FROM lists").fetchone()[0]
    return {
        "total": total,
        "read": read,
        "avg_rating": round(avg_rating, 1) if avg_rating else None,
        "total_lists": total_lists,
    }


# ---------------------------------------------------------------------------
# GÉNEROS
# ---------------------------------------------------------------------------

def get_all_genres():
    db = get_db()
    return db.execute("SELECT * FROM genres ORDER BY name COLLATE NOCASE").fetchall()


def get_genres_for_book(book_id):
    db = get_db()
    return db.execute(
        """SELECT genres.* FROM genres
           JOIN book_genres ON genres.id = book_genres.genre_id
           WHERE book_genres.book_id = ?
           ORDER BY genres.name COLLATE NOCASE""",
        (book_id,),
    ).fetchall()


def get_or_create_genre(name):
    """Busca un género por nombre (sin importar mayúsculas) o lo crea si no existe."""
    name = name.strip()
    if not name:
        return None
    db = get_db()
    row = db.execute("SELECT id FROM genres WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
    if row:
        return row["id"]
    cur = db.execute("INSERT INTO genres (name) VALUES (?)", (name,))
    db.commit()
    return cur.lastrowid


def set_book_genres(book_id, genre_ids):
    """Reemplaza los géneros asociados a un libro. Se limita a MAX_GENRES_PER_BOOK."""
    db = get_db()
    genre_ids = list(dict.fromkeys(genre_ids))[:MAX_GENRES_PER_BOOK]  # únicos, en orden, con tope
    db.execute("DELETE FROM book_genres WHERE book_id = ?", (book_id,))
    db.executemany(
        "INSERT OR IGNORE INTO book_genres (book_id, genre_id) VALUES (?, ?)",
        [(book_id, gid) for gid in genre_ids],
    )
    db.commit()


# ---------------------------------------------------------------------------
# LISTAS ("libretas")
# ---------------------------------------------------------------------------

def create_list(name, color, description=None, background_path=None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO lists (name, color, description, background_path) VALUES (?, ?, ?, ?)",
        (name, color, description, background_path),
    )
    db.commit()
    return cur.lastrowid


def update_list(list_id, name, color, description=None, background_path=None, keep_background=True):
    db = get_db()
    if keep_background:
        db.execute(
            "UPDATE lists SET name=?, color=?, description=? WHERE id=?",
            (name, color, description, list_id),
        )
    else:
        db.execute(
            "UPDATE lists SET name=?, color=?, description=?, background_path=? WHERE id=?",
            (name, color, description, background_path, list_id),
        )
    db.commit()


def delete_list(list_id):
    db = get_db()
    db.execute("DELETE FROM lists WHERE id=?", (list_id,))
    db.commit()


def get_list(list_id):
    db = get_db()
    return db.execute("SELECT * FROM lists WHERE id=?", (list_id,)).fetchone()


def get_all_lists():
    db = get_db()
    return db.execute(
        """SELECT lists.*, COUNT(list_books.book_id) AS book_count
           FROM lists
           LEFT JOIN list_books ON lists.id = list_books.list_id
           GROUP BY lists.id
           ORDER BY lists.created_at DESC"""
    ).fetchall()


def get_books_in_list(list_id, sort="added", order="desc"):
    db = get_db()
    col = SORT_COLUMNS.get(sort, "id")
    order = "ASC" if order == "asc" else "DESC"
    query = f"""SELECT books.* FROM books
                JOIN list_books ON books.id = list_books.book_id
                WHERE list_books.list_id = ?
                ORDER BY {col} {order}"""
    return db.execute(query, (list_id,)).fetchall()


def get_books_not_in_list(list_id):
    db = get_db()
    return db.execute(
        """SELECT * FROM books
           WHERE id NOT IN (SELECT book_id FROM list_books WHERE list_id = ?)
           ORDER BY title COLLATE NOCASE""",
        (list_id,),
    ).fetchall()


def add_book_to_list(list_id, book_id):
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO list_books (list_id, book_id) VALUES (?, ?)",
        (list_id, book_id),
    )
    db.commit()


def remove_book_from_list(list_id, book_id):
    db = get_db()
    db.execute(
        "DELETE FROM list_books WHERE list_id=? AND book_id=?", (list_id, book_id)
    )
    db.commit()
