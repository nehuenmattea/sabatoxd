"""
database.py
Capa de acceso a datos para Sábatoxd.
Usa sqlite3 puro (sin ORM) para mantener la app simple y sin dependencias extra.
"""

import sqlite3
import os
import sys
from flask import g


def get_data_dir():
    """Carpeta donde se guardan los datos del usuario (base de datos e imágenes).

    - En modo desarrollo (python app.py): la carpeta del proyecto, como antes.
    - En modo empaquetado (ejecutable de PyInstaller): una carpeta persistente
      fuera del ejecutable (que es de solo lectura y se borra/reemplaza en
      cada actualización), para que los datos del usuario no se pierdan.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        elif sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support")
        else:
            base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        data_dir = os.path.join(base, "Sabatoxd")
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "estanteria.db")

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

        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE
        );

        CREATE TABLE IF NOT EXISTS book_authors (
            book_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (book_id, author_id),
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS book_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            date_read TEXT,
            rating REAL DEFAULT 0,
            note TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS list_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL DEFAULT 'guest',
            photo_path TEXT,
            bio TEXT,
            fav_book_1 INTEGER,
            fav_book_2 INTEGER,
            fav_book_3 INTEGER,
            fav_book_4 INTEGER
        );
        """
    )

    # Migraciones para bases de datos creadas con versiones anteriores
    _ensure_column(conn, "lists", "background_path", "TEXT")
    _ensure_column(conn, "lists", "description", "TEXT")
    _ensure_column(conn, "books", "description", "TEXT")

    # Sembrar géneros por defecto solo si la tabla está vacía
    count = conn.execute("SELECT COUNT(*) FROM genres").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT OR IGNORE INTO genres (name) VALUES (?)",
            [(g,) for g in DEFAULT_GENRES],
        )

    # Fila única de perfil, por defecto "guest"
    prof_count = conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0]
    if prof_count == 0:
        conn.execute("INSERT INTO profile (id, username) VALUES (1, 'guest')")

    # Migración: libros viejos con author de texto libre pero sin fila en
    # book_authors todavía (bases de datos de versiones anteriores).
    orphan_authors = conn.execute(
        """SELECT id, author FROM books
           WHERE author IS NOT NULL AND TRIM(author) != ''
             AND id NOT IN (SELECT DISTINCT book_id FROM book_authors)"""
    ).fetchall()
    for book_id, author_text in orphan_authors:
        for pos, name in enumerate(_split_names(author_text)):
            row = conn.execute(
                "SELECT id FROM authors WHERE name = ? COLLATE NOCASE", (name,)
            ).fetchone()
            if row:
                author_id = row[0]
            else:
                author_id = conn.execute(
                    "INSERT INTO authors (name) VALUES (?)", (name,)
                ).lastrowid
            conn.execute(
                "INSERT OR IGNORE INTO book_authors (book_id, author_id, position) VALUES (?, ?, ?)",
                (book_id, author_id, pos),
            )

    # Migración: libros viejos con rating/date_read directo pero sin fila en
    # book_readings todavía.
    orphan_readings = conn.execute(
        """SELECT id, date_read, rating FROM books
           WHERE (rating IS NOT NULL AND rating > 0) OR (date_read IS NOT NULL AND date_read != '')
             AND id NOT IN (SELECT DISTINCT book_id FROM book_readings)"""
    ).fetchall()
    for book_id, date_read, rating in orphan_readings:
        exists = conn.execute(
            "SELECT COUNT(*) FROM book_readings WHERE book_id = ?", (book_id,)
        ).fetchone()[0]
        if not exists:
            conn.execute(
                "INSERT INTO book_readings (book_id, date_read, rating) VALUES (?, ?, ?)",
                (book_id, date_read, rating or 0),
            )

    conn.commit()
    conn.close()


def _split_names(raw):
    """Divide un texto de autores/nombres separados por coma en una lista limpia."""
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


# ---------------------------------------------------------------------------
# LIBROS
# ---------------------------------------------------------------------------

def create_book(title, year, pages, description, cover_path):
    db = get_db()
    cur = db.execute(
        """INSERT INTO books (title, author, year, pages, description, date_read, rating, cover_path)
           VALUES (?, '', ?, ?, ?, NULL, 0, ?)""",
        (title, year, pages, description, cover_path),
    )
    db.commit()
    return cur.lastrowid


def update_book(book_id, title, year, pages, description, cover_path=None, keep_cover=True):
    db = get_db()
    if keep_cover:
        db.execute(
            """UPDATE books SET title=?, year=?, pages=?, description=?
               WHERE id=?""",
            (title, year, pages, description, book_id),
        )
    else:
        db.execute(
            """UPDATE books SET title=?, year=?, pages=?, description=?, cover_path=?
               WHERE id=?""",
            (title, year, pages, description, cover_path, book_id),
        )
    db.commit()


def delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM books WHERE id=?", (book_id,))
    db.commit()


def get_book(book_id):
    db = get_db()
    return db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()


def get_all_books(sort="added", order="desc", rating_filter="", search="", genre_filter="", author_filter=""):
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

    if author_filter:
        query += """ AND books.id IN (
            SELECT book_id FROM book_authors WHERE author_id = ?
        )"""
        params.append(int(author_filter))

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
# AUTORES
# ---------------------------------------------------------------------------

def get_or_create_author(name):
    """Busca un autor por nombre (sin importar mayúsculas) o lo crea si no existe."""
    name = name.strip()
    if not name:
        return None
    db = get_db()
    row = db.execute("SELECT id FROM authors WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
    if row:
        return row["id"]
    cur = db.execute("INSERT INTO authors (name) VALUES (?)", (name,))
    db.commit()
    return cur.lastrowid


def set_book_authors(book_id, names):
    """Reemplaza los autores de un libro a partir de una lista de nombres (en orden).
    También actualiza la columna books.author (texto plano) que se usa como caché
    para ordenar y buscar."""
    db = get_db()
    names = list(dict.fromkeys([n.strip() for n in names if n.strip()]))  # únicos, en orden

    author_ids = [get_or_create_author(n) for n in names]

    db.execute("DELETE FROM book_authors WHERE book_id = ?", (book_id,))
    db.executemany(
        "INSERT OR IGNORE INTO book_authors (book_id, author_id, position) VALUES (?, ?, ?)",
        [(book_id, aid, i) for i, aid in enumerate(author_ids) if aid],
    )
    db.execute("UPDATE books SET author=? WHERE id=?", (", ".join(names), book_id))
    db.commit()


def get_authors_for_book(book_id):
    db = get_db()
    return db.execute(
        """SELECT authors.* FROM authors
           JOIN book_authors ON authors.id = book_authors.author_id
           WHERE book_authors.book_id = ?
           ORDER BY book_authors.position""",
        (book_id,),
    ).fetchall()


def get_all_authors():
    db = get_db()
    return db.execute(
        """SELECT authors.*, COUNT(book_authors.book_id) AS book_count
           FROM authors
           LEFT JOIN book_authors ON authors.id = book_authors.author_id
           GROUP BY authors.id
           ORDER BY authors.name COLLATE NOCASE"""
    ).fetchall()


def get_author(author_id):
    db = get_db()
    return db.execute("SELECT * FROM authors WHERE id=?", (author_id,)).fetchone()


def get_books_by_author(author_id):
    db = get_db()
    return db.execute(
        """SELECT books.* FROM books
           JOIN book_authors ON books.id = book_authors.book_id
           WHERE book_authors.author_id = ?
           ORDER BY books.title COLLATE NOCASE""",
        (author_id,),
    ).fetchall()


# ---------------------------------------------------------------------------
# LECTURAS (calificaciones múltiples por libro)
# ---------------------------------------------------------------------------

def get_readings_for_book(book_id):
    db = get_db()
    return db.execute(
        """SELECT * FROM book_readings WHERE book_id = ?
           ORDER BY (date_read IS NULL), date_read DESC, id DESC""",
        (book_id,),
    ).fetchall()


def get_reading(reading_id):
    db = get_db()
    return db.execute("SELECT * FROM book_readings WHERE id=?", (reading_id,)).fetchone()


def add_reading(book_id, date_read, rating, note=None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO book_readings (book_id, date_read, rating, note) VALUES (?, ?, ?, ?)",
        (book_id, date_read, rating, note),
    )
    db.commit()
    recompute_book_rating(book_id)
    return cur.lastrowid


def update_reading(reading_id, date_read, rating, note=None):
    db = get_db()
    reading = get_reading(reading_id)
    db.execute(
        "UPDATE book_readings SET date_read=?, rating=?, note=? WHERE id=?",
        (date_read, rating, note, reading_id),
    )
    db.commit()
    if reading:
        recompute_book_rating(reading["book_id"])


def delete_reading(reading_id):
    db = get_db()
    reading = get_reading(reading_id)
    db.execute("DELETE FROM book_readings WHERE id=?", (reading_id,))
    db.commit()
    if reading:
        recompute_book_rating(reading["book_id"])


def recompute_book_rating(book_id):
    """Recalcula books.rating y books.date_read (usados para ordenar/filtrar
    rápido) a partir de la lectura más reciente del libro."""
    db = get_db()
    latest = db.execute(
        """SELECT date_read, rating FROM book_readings WHERE book_id = ?
           ORDER BY (date_read IS NULL), date_read DESC, id DESC LIMIT 1""",
        (book_id,),
    ).fetchone()
    if latest:
        db.execute(
            "UPDATE books SET rating=?, date_read=? WHERE id=?",
            (latest["rating"] or 0, latest["date_read"], book_id),
        )
    else:
        db.execute("UPDATE books SET rating=0, date_read=NULL WHERE id=?", (book_id,))
    db.commit()


# ---------------------------------------------------------------------------
# GÉNEROS
# ---------------------------------------------------------------------------

def get_all_genres():
    db = get_db()
    return db.execute(
        """SELECT genres.*, COUNT(book_genres.book_id) AS book_count
           FROM genres
           LEFT JOIN book_genres ON genres.id = book_genres.genre_id
           GROUP BY genres.id
           ORDER BY genres.name COLLATE NOCASE"""
    ).fetchall()


def get_genre(genre_id):
    db = get_db()
    return db.execute("SELECT * FROM genres WHERE id=?", (genre_id,)).fetchone()


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


def rename_genre(genre_id, name):
    name = name.strip()
    if not name:
        return False
    db = get_db()
    exists = db.execute(
        "SELECT id FROM genres WHERE name = ? COLLATE NOCASE AND id != ?", (name, genre_id)
    ).fetchone()
    if exists:
        return False
    db.execute("UPDATE genres SET name=? WHERE id=?", (name, genre_id))
    db.commit()
    return True


def delete_genre(genre_id):
    db = get_db()
    db.execute("DELETE FROM genres WHERE id=?", (genre_id,))
    db.commit()


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


def is_book_in_list(list_id, book_id):
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM list_books WHERE list_id=? AND book_id=?", (list_id, book_id)
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# NOTAS DE TEXTO LIBRE EN UNA LIBRETA (bloc de notas, sin necesidad de libro)
# ---------------------------------------------------------------------------

def get_notes_for_list(list_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM list_notes WHERE list_id=? ORDER BY done, created_at DESC",
        (list_id,),
    ).fetchall()


def add_list_note(list_id, text):
    text = (text or "").strip()
    if not text:
        return None
    db = get_db()
    cur = db.execute(
        "INSERT INTO list_notes (list_id, text) VALUES (?, ?)", (list_id, text)
    )
    db.commit()
    return cur.lastrowid


def toggle_list_note(note_id):
    db = get_db()
    db.execute("UPDATE list_notes SET done = 1 - done WHERE id=?", (note_id,))
    db.commit()


def delete_list_note(note_id):
    db = get_db()
    db.execute("DELETE FROM list_notes WHERE id=?", (note_id,))
    db.commit()


def get_note(note_id):
    db = get_db()
    return db.execute("SELECT * FROM list_notes WHERE id=?", (note_id,)).fetchone()


# ---------------------------------------------------------------------------
# REGISTRO DE ACTIVIDAD (logs)
# ---------------------------------------------------------------------------

def log_activity(action, message):
    db = get_db()
    db.execute(
        "INSERT INTO activity_log (action, message) VALUES (?, ?)", (action, message)
    )
    db.commit()


def get_activity_log(limit=300):
    db = get_db()
    return db.execute(
        "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()


def clear_activity_log():
    db = get_db()
    db.execute("DELETE FROM activity_log")
    db.commit()


# ---------------------------------------------------------------------------
# PERFIL
# ---------------------------------------------------------------------------

def get_profile():
    db = get_db()
    row = db.execute("SELECT * FROM profile WHERE id=1").fetchone()
    if row is None:
        db.execute("INSERT OR IGNORE INTO profile (id, username) VALUES (1, 'guest')")
        db.commit()
        row = db.execute("SELECT * FROM profile WHERE id=1").fetchone()
    return row


def update_profile(username, bio=None, photo_path=None, keep_photo=True,
                    fav_book_1=None, fav_book_2=None, fav_book_3=None, fav_book_4=None):
    db = get_db()
    if keep_photo:
        db.execute(
            """UPDATE profile SET username=?, bio=?, fav_book_1=?, fav_book_2=?,
               fav_book_3=?, fav_book_4=? WHERE id=1""",
            (username, bio, fav_book_1, fav_book_2, fav_book_3, fav_book_4),
        )
    else:
        db.execute(
            """UPDATE profile SET username=?, bio=?, photo_path=?, fav_book_1=?,
               fav_book_2=?, fav_book_3=?, fav_book_4=? WHERE id=1""",
            (username, bio, photo_path, fav_book_1, fav_book_2, fav_book_3, fav_book_4),
        )
    db.commit()


def get_favorite_books():
    """Devuelve los hasta 4 libros favoritos del perfil, en orden, salteando huecos."""
    profile = get_profile()
    ids = [profile["fav_book_1"], profile["fav_book_2"], profile["fav_book_3"], profile["fav_book_4"]]
    books = []
    for bid in ids:
        if bid:
            b = get_book(bid)
            if b:
                books.append(b)
    return books
