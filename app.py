"""
Sábatoxd
Aplicación local para registrar libros, calificarlos y organizarlos en listas.
Ejecutar con: python app.py
Luego abrir: http://127.0.0.1:5000
"""

import os
import sys
import uuid
import shutil
import sqlite3
import webbrowser
import threading
from datetime import date

from flask import (
    Flask, render_template, request, redirect, url_for, flash, abort,
    send_from_directory, send_file, jsonify,
)
from werkzeug.utils import secure_filename

import database as db

# Carpeta con el código (dentro del ejecutable si está empaquetado; de solo lectura).
# Ahí viven las plantillas y el CSS/JS, que no cambian en tiempo de ejecución.
if getattr(sys, "frozen", False):
    RESOURCE_DIR = sys._MEIPASS
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpeta persistente donde se guardan los datos del usuario (portadas, fondos).
# En modo desarrollo es la misma carpeta del proyecto; empaquetada, una carpeta
# aparte que sobrevive a las actualizaciones del ejecutable (ver database.py).
DATA_DIR = db.DATA_DIR
COVERS_FOLDER = os.path.join(DATA_DIR, "static", "covers")
BACKGROUNDS_FOLDER = os.path.join(DATA_DIR, "static", "list_backgrounds")
PROFILE_FOLDER = os.path.join(DATA_DIR, "static", "profile")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_DB_EXTENSIONS = {"db", "sqlite", "sqlite3"}

os.makedirs(COVERS_FOLDER, exist_ok=True)
os.makedirs(BACKGROUNDS_FOLDER, exist_ok=True)
os.makedirs(PROFILE_FOLDER, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(RESOURCE_DIR, "templates"),
    static_folder=os.path.join(RESOURCE_DIR, "static"),
)
app.secret_key = "estanteria-local-secret"  # solo se usa para mensajes flash locales
app.teardown_appcontext(db.close_db)

# Colores de placeholder para portadas no subidas (tonos papel cálidos)
PLACEHOLDER_COLORS = [
    "#E7D9C2", "#D9C7B0", "#E0D3BE", "#CBB89C",
    "#DCCBB5", "#D4C0A5", "#E3D6C0", "#CDBBA1",
]


def placeholder_color(title):
    h = sum(ord(c) for c in (title or "?"))
    return PLACEHOLDER_COLORS[h % len(PLACEHOLDER_COLORS)]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage, folder):
    """Guarda un archivo de imagen subido en la carpeta indicada y devuelve el nombre generado."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(folder, filename))
    return filename


def delete_upload(filename, folder):
    if not filename:
        return
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def save_cover(file_storage):
    return save_upload(file_storage, COVERS_FOLDER)


def delete_cover_file(filename):
    delete_upload(filename, COVERS_FOLDER)


def save_background(file_storage):
    return save_upload(file_storage, BACKGROUNDS_FOLDER)


def delete_background_file(filename):
    delete_upload(filename, BACKGROUNDS_FOLDER)


def save_profile_photo(file_storage):
    return save_upload(file_storage, PROFILE_FOLDER)


def delete_profile_photo_file(filename):
    delete_upload(filename, PROFILE_FOLDER)


@app.route("/uploads/covers/<path:filename>")
def cover_file(filename):
    return send_from_directory(COVERS_FOLDER, filename)


@app.route("/uploads/backgrounds/<path:filename>")
def background_file(filename):
    return send_from_directory(BACKGROUNDS_FOLDER, filename)


@app.route("/uploads/profile/<path:filename>")
def profile_photo_file(filename):
    return send_from_directory(PROFILE_FOLDER, filename)


# Filtros / globals de Jinja
app.jinja_env.globals["placeholder_color"] = placeholder_color
app.jinja_env.globals["list_colors"] = db.LIST_COLORS
app.jinja_env.globals["color_hex"] = lambda name: db.COLOR_HEX_MAP.get(name, "#707885")
app.jinja_env.globals["rating_options"] = db.RATING_OPTIONS
app.jinja_env.globals["max_genres"] = db.MAX_GENRES_PER_BOOK


@app.context_processor
def inject_profile():
    """Deja el perfil disponible en todas las plantillas (foto/nombre en el header)."""
    try:
        return {"current_profile": db.get_profile()}
    except sqlite3.OperationalError:
        return {"current_profile": None}


def format_rating(value):
    """4.0 -> '4' · 4.5 -> '4.5' (para mostrar en labels de filtros)."""
    if value is None:
        return ""
    value = float(value)
    return str(int(value)) if value.is_integer() else str(value)


app.jinja_env.filters["fmt_rating"] = format_rating


def today_iso():
    return date.today().isoformat()


def parse_book_form(form):
    """Extrae y normaliza los datos generales del formulario de libro
    (sin autores ni calificación/fecha, que se manejan aparte).
    Devuelve (data, error) — error es un mensaje si algo no es válido."""
    title = form.get("title", "").strip()
    year = form.get("year", "").strip()
    pages = form.get("pages", "").strip()
    description = form.get("description", "").strip()

    error = None

    return {
        "title": title,
        "year": int(year) if year.isdigit() else None,
        "pages": int(pages) if pages.isdigit() else None,
        "description": description or None,
    }, error


def parse_authors_form(form):
    """Autores separados por coma escritos en un único campo de texto."""
    raw = form.get("authors", "").strip()
    names = db._split_names(raw)
    return names[:10]  # tope razonable


def parse_genres_form(form):
    """Combina los géneros tildados con los nuevos escritos a mano (separados por coma).
    Devuelve (genre_ids, warning) — warning avisa si se recortó por superar el máximo."""
    genre_ids = []
    for gid in form.getlist("genres"):
        if gid.isdigit():
            genre_ids.append(int(gid))

    new_genres_raw = form.get("new_genres", "").strip()
    if new_genres_raw:
        for name in new_genres_raw.split(","):
            name = name.strip()
            if name:
                gid = db.get_or_create_genre(name)
                if gid:
                    genre_ids.append(gid)

    genre_ids = list(dict.fromkeys(genre_ids))  # sin duplicados, conserva el orden
    warning = None
    if len(genre_ids) > db.MAX_GENRES_PER_BOOK:
        warning = f"Un libro puede tener hasta {db.MAX_GENRES_PER_BOOK} géneros; se guardaron los primeros {db.MAX_GENRES_PER_BOOK}."
        genre_ids = genre_ids[: db.MAX_GENRES_PER_BOOK]

    return genre_ids, warning


def parse_reading_form(form):
    """Extrae fecha/calificación/nota de un formulario de 'lectura'.
    Devuelve (date_read, rating, note, error)."""
    date_read = form.get("date_read", "").strip() or None
    rating_raw = form.get("rating", "0").strip()
    note = form.get("note", "").strip() or None

    error = None
    if date_read and date_read > today_iso():
        error = "La fecha de lectura no puede ser posterior al día de hoy."

    try:
        rating = float(rating_raw) if rating_raw else 0.0
        rating = round(rating * 2) / 2
        rating = max(0.0, min(5.0, rating))
    except ValueError:
        rating = 0.0

    return date_read, rating, note, error


# ---------------------------------------------------------------------------
# INICIO / LIBROS
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    sort = request.args.get("sort", "added")
    order = request.args.get("order", "desc")
    rating_filter = request.args.get("rating", "")
    genre_filter = request.args.get("genre", "")
    author_filter = request.args.get("author", "")
    q = request.args.get("q", "").strip()

    books = db.get_all_books(
        sort=sort, order=order, rating_filter=rating_filter,
        search=q, genre_filter=genre_filter, author_filter=author_filter,
    )
    stats = db.get_stats()
    genres = db.get_all_genres()

    return render_template(
        "index.html",
        books=books,
        sort=sort,
        order=order,
        rating_filter=rating_filter,
        genre_filter=genre_filter,
        author_filter=author_filter,
        q=q,
        stats=stats,
        genres=genres,
    )


@app.route("/libro/nuevo", methods=["GET", "POST"])
def new_book():
    if request.method == "POST":
        data, error = parse_book_form(request.form)
        genre_ids, genre_warning = parse_genres_form(request.form)
        author_names = parse_authors_form(request.form)
        date_read, rating, reading_note, reading_error = parse_reading_form(request.form)

        if not data["title"]:
            error = "El título es obligatorio."
        elif reading_error:
            error = reading_error

        if error:
            flash(error, "error")
            return render_template(
                "book_form.html", book=None, form_data=data,
                genres=db.get_all_genres(), selected_genre_ids=genre_ids,
                authors_text=request.form.get("authors", ""), today=today_iso(),
            )

        if genre_warning:
            flash(genre_warning, "error")

        cover_filename = save_cover(request.files.get("cover"))
        book_id = db.create_book(
            data["title"], data["year"], data["pages"], data["description"], cover_filename,
        )
        db.set_book_genres(book_id, genre_ids)
        db.set_book_authors(book_id, author_names)

        if rating > 0 or date_read:
            db.add_reading(book_id, date_read, rating, reading_note)

        db.log_activity("book_added", f'Se agregó el libro "{data["title"]}".')

        # Si se abrió el formulario desde una lista específica, agregarlo ahí
        add_to_list = request.args.get("list_id") or request.form.get("list_id")
        if add_to_list:
            db.add_book_to_list(int(add_to_list), book_id)
            return redirect(url_for("list_detail", list_id=add_to_list))

        flash(f'"{data["title"]}" se agregó a tu estantería.', "success")
        return redirect(url_for("book_detail", book_id=book_id))

    return render_template(
        "book_form.html", book=None, form_data=None,
        genres=db.get_all_genres(), selected_genre_ids=[], authors_text="", today=today_iso(),
    )


@app.route("/libro/<int:book_id>")
def book_detail(book_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)
    lists = db.get_lists_for_book(book_id)
    genres = db.get_genres_for_book(book_id)
    authors = db.get_authors_for_book(book_id)
    readings = db.get_readings_for_book(book_id)
    return render_template(
        "book_detail.html", book=book, lists=lists, genres=genres,
        authors=authors, readings=readings,
    )


@app.route("/libro/<int:book_id>/editar", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)

    if request.method == "POST":
        data, error = parse_book_form(request.form)
        genre_ids, genre_warning = parse_genres_form(request.form)
        author_names = parse_authors_form(request.form)

        if not data["title"]:
            error = "El título es obligatorio."

        if error:
            flash(error, "error")
            return render_template(
                "book_form.html", book=book, form_data=data,
                genres=db.get_all_genres(), selected_genre_ids=genre_ids,
                authors_text=request.form.get("authors", ""), today=today_iso(),
            )

        if genre_warning:
            flash(genre_warning, "error")

        remove_cover = request.form.get("remove_cover") == "1"
        new_cover = save_cover(request.files.get("cover"))

        if new_cover:
            delete_cover_file(book["cover_path"])
            db.update_book(book_id, data["title"], data["year"], data["pages"],
                            data["description"], cover_path=new_cover, keep_cover=False)
        elif remove_cover:
            delete_cover_file(book["cover_path"])
            db.update_book(book_id, data["title"], data["year"], data["pages"],
                            data["description"], cover_path=None, keep_cover=False)
        else:
            db.update_book(book_id, data["title"], data["year"], data["pages"],
                            data["description"], keep_cover=True)

        db.set_book_genres(book_id, genre_ids)
        db.set_book_authors(book_id, author_names)

        db.log_activity("book_edited", f'Se editó el libro "{data["title"]}".')

        flash(f'"{data["title"]}" se actualizó.', "success")
        return redirect(url_for("book_detail", book_id=book_id))

    current_genre_ids = [g["id"] for g in db.get_genres_for_book(book_id)]
    current_authors = ", ".join(a["name"] for a in db.get_authors_for_book(book_id))
    return render_template(
        "book_form.html", book=book, form_data=None,
        genres=db.get_all_genres(), selected_genre_ids=current_genre_ids,
        authors_text=current_authors, today=today_iso(),
    )


@app.route("/libro/<int:book_id>/borrar", methods=["POST"])
def delete_book(book_id):
    book = db.get_book(book_id)
    if book:
        delete_cover_file(book["cover_path"])
        db.delete_book(book_id)
        db.log_activity("book_deleted", f'Se eliminó el libro "{book["title"]}".')
        flash(f'"{book["title"]}" se eliminó de tu estantería.', "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# LECTURAS (calificaciones múltiples de un libro)
# ---------------------------------------------------------------------------

@app.route("/libro/<int:book_id>/lectura/nueva", methods=["POST"])
def new_reading(book_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)
    date_read, rating, note, error = parse_reading_form(request.form)
    if error:
        flash(error, "error")
    else:
        db.add_reading(book_id, date_read, rating, note)
        db.log_activity("reading_added", f'Se agregó una lectura de "{book["title"]}".')
        flash("Lectura agregada.", "success")
    return redirect(url_for("book_detail", book_id=book_id))


@app.route("/libro/<int:book_id>/lectura/<int:reading_id>/editar", methods=["POST"])
def edit_reading(book_id, reading_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)
    date_read, rating, note, error = parse_reading_form(request.form)
    if error:
        flash(error, "error")
    else:
        db.update_reading(reading_id, date_read, rating, note)
        db.log_activity("reading_edited", f'Se editó una lectura de "{book["title"]}".')
        flash("Lectura actualizada.", "success")
    return redirect(url_for("book_detail", book_id=book_id))


@app.route("/libro/<int:book_id>/lectura/<int:reading_id>/borrar", methods=["POST"])
def delete_reading_route(book_id, reading_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)
    db.delete_reading(reading_id)
    db.log_activity("reading_deleted", f'Se eliminó una lectura de "{book["title"]}".')
    flash("Lectura eliminada.", "success")
    return redirect(url_for("book_detail", book_id=book_id))


# ---------------------------------------------------------------------------
# LISTAS ("libretas")
# ---------------------------------------------------------------------------

@app.route("/listas")
def lists_view():
    lists = db.get_all_lists()
    return render_template("lists.html", lists=lists)


@app.route("/listas/nueva", methods=["GET", "POST"])
def new_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        color = request.form.get("color", "azul")
        description = request.form.get("description", "").strip() or None

        if not name:
            flash("La libreta necesita un nombre.", "error")
            return render_template("list_form.html", list=None)
        if color not in db.COLOR_HEX_MAP:
            color = "azul"

        background_filename = save_background(request.files.get("background"))
        list_id = db.create_list(name, color, description=description, background_path=background_filename)
        db.log_activity("list_created", f'Se creó la libreta "{name}".')
        flash(f'Libreta "{name}" creada.', "success")
        return redirect(url_for("list_detail", list_id=list_id))

    return render_template("list_form.html", list=None)


@app.route("/listas/<int:list_id>")
def list_detail(list_id):
    lst = db.get_list(list_id)
    if not lst:
        abort(404)
    sort = request.args.get("sort", "added")
    order = request.args.get("order", "desc")
    books = db.get_books_in_list(list_id, sort=sort, order=order)
    in_list_ids = {b["id"] for b in books}

    available_books = db.get_books_not_in_list(list_id)
    available_books_json = [
        {"id": b["id"], "title": b["title"], "author": b["author"] or "", "year": b["year"]}
        for b in available_books
    ]

    all_books = db.get_all_books(sort="title", order="asc")
    picker_books_json = [
        {
            "id": b["id"],
            "title": b["title"],
            "author": b["author"] or "",
            "year": b["year"],
            "cover_url": url_for("cover_file", filename=b["cover_path"]) if b["cover_path"] else None,
            "in_list": b["id"] in in_list_ids,
        }
        for b in all_books
    ]
    notes = db.get_notes_for_list(list_id)
    return render_template(
        "list_detail.html",
        list=lst,
        books=books,
        sort=sort,
        order=order,
        available_books_json=available_books_json,
        picker_books_json=picker_books_json,
        has_available=len(available_books) > 0,
        has_any_books=len(all_books) > 0,
        notes=notes,
    )


@app.route("/listas/<int:list_id>/editar", methods=["GET", "POST"])
def edit_list(list_id):
    lst = db.get_list(list_id)
    if not lst:
        abort(404)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        color = request.form.get("color", lst["color"])
        description = request.form.get("description", "").strip() or None

        if not name:
            flash("La libreta necesita un nombre.", "error")
            return render_template("list_form.html", list=lst)
        if color not in db.COLOR_HEX_MAP:
            color = lst["color"]

        remove_background = request.form.get("remove_background") == "1"
        new_background = save_background(request.files.get("background"))

        if new_background:
            delete_background_file(lst["background_path"])
            db.update_list(list_id, name, color, description=description,
                            background_path=new_background, keep_background=False)
        elif remove_background:
            delete_background_file(lst["background_path"])
            db.update_list(list_id, name, color, description=description,
                            background_path=None, keep_background=False)
        else:
            db.update_list(list_id, name, color, description=description, keep_background=True)

        db.log_activity("list_edited", f'Se editó la libreta "{name}".')
        flash("Libreta actualizada.", "success")
        return redirect(url_for("list_detail", list_id=list_id))
    return render_template("list_form.html", list=lst)


@app.route("/listas/<int:list_id>/borrar", methods=["POST"])
def delete_list(list_id):
    lst = db.get_list(list_id)
    if lst:
        delete_background_file(lst["background_path"])
        db.delete_list(list_id)
        db.log_activity("list_deleted", f'Se eliminó la libreta "{lst["name"]}".')
        flash(f'Libreta "{lst["name"]}" eliminada (los libros no se borraron).', "success")
    return redirect(url_for("lists_view"))


@app.route("/listas/<int:list_id>/agregar", methods=["POST"])
def add_book_to_list(list_id):
    book_id = request.form.get("book_id", "")
    if book_id.isdigit():
        db.add_book_to_list(list_id, int(book_id))
        db.log_activity("list_book_added", "Se agregó un libro a una libreta.")
        flash("Libro agregado a la lista.", "success")
    else:
        flash("Elegí un libro de la lista de resultados antes de agregar.", "error")
    return redirect(url_for("list_detail", list_id=list_id))


@app.route("/listas/<int:list_id>/quitar/<int:book_id>", methods=["POST"])
def remove_book_from_list(list_id, book_id):
    db.remove_book_from_list(list_id, book_id)
    db.log_activity("list_book_removed", "Se quitó un libro de una libreta.")
    flash("Libro quitado de la lista.", "success")
    return redirect(url_for("list_detail", list_id=list_id))


@app.route("/listas/<int:list_id>/alternar/<int:book_id>", methods=["POST"])
def toggle_book_in_list_ajax(list_id, book_id):
    """Agrega o quita un libro de la libreta vía AJAX, para el selector visual
    con clicks (se van 'atenuando' los que ya están agregados)."""
    lst = db.get_list(list_id)
    book = db.get_book(book_id)
    if not lst or not book:
        return jsonify({"ok": False, "error": "No encontrado"}), 404

    if db.is_book_in_list(list_id, book_id):
        db.remove_book_from_list(list_id, book_id)
        db.log_activity("list_book_removed", f'Se quitó "{book["title"]}" de "{lst["name"]}".')
        in_list = False
    else:
        db.add_book_to_list(list_id, book_id)
        db.log_activity("list_book_added", f'Se agregó "{book["title"]}" a "{lst["name"]}".')
        in_list = True

    return jsonify({"ok": True, "in_list": in_list, "book_id": book_id})


# ---------------------------------------------------------------------------
# NOTAS DE TEXTO LIBRE DENTRO DE UNA LIBRETA
# ---------------------------------------------------------------------------

@app.route("/listas/<int:list_id>/notas/nueva", methods=["POST"])
def new_list_note(list_id):
    lst = db.get_list(list_id)
    if not lst:
        abort(404)
    text = request.form.get("text", "").strip()
    if text:
        db.add_list_note(list_id, text)
    return redirect(url_for("list_detail", list_id=list_id))


@app.route("/listas/<int:list_id>/notas/<int:note_id>/alternar", methods=["POST"])
def toggle_note_route(list_id, note_id):
    db.toggle_list_note(note_id)
    return redirect(url_for("list_detail", list_id=list_id))


@app.route("/listas/<int:list_id>/notas/<int:note_id>/borrar", methods=["POST"])
def delete_note_route(list_id, note_id):
    db.delete_list_note(note_id)
    return redirect(url_for("list_detail", list_id=list_id))


# ---------------------------------------------------------------------------
# GÉNEROS
# ---------------------------------------------------------------------------

@app.route("/generos")
def genres_view():
    genres = db.get_all_genres()
    return render_template("genres.html", genres=genres)


@app.route("/generos/<int:genre_id>/renombrar", methods=["POST"])
def rename_genre_route(genre_id):
    genre = db.get_genre(genre_id)
    if not genre:
        abort(404)
    new_name = request.form.get("name", "").strip()
    if not new_name:
        flash("El género necesita un nombre.", "error")
    elif db.rename_genre(genre_id, new_name):
        db.log_activity("genre_renamed", f'Se renombró el género "{genre["name"]}" a "{new_name}".')
        flash("Género actualizado.", "success")
    else:
        flash(f'Ya existe un género llamado "{new_name}".', "error")
    return redirect(url_for("genres_view"))


@app.route("/generos/<int:genre_id>/borrar", methods=["POST"])
def delete_genre_route(genre_id):
    genre = db.get_genre(genre_id)
    if genre:
        db.delete_genre(genre_id)
        db.log_activity("genre_deleted", f'Se eliminó el género "{genre["name"]}".')
        flash(f'Género "{genre["name"]}" eliminado.', "success")
    return redirect(url_for("genres_view"))


# ---------------------------------------------------------------------------
# AUTORES
# ---------------------------------------------------------------------------

@app.route("/autores")
def authors_view():
    authors = db.get_all_authors()
    return render_template("authors.html", authors=authors)


@app.route("/autores/<int:author_id>")
def author_detail(author_id):
    author = db.get_author(author_id)
    if not author:
        abort(404)
    books = db.get_books_by_author(author_id)
    return render_template("author_detail.html", author=author, books=books)


# ---------------------------------------------------------------------------
# ACTIVIDAD (logs)
# ---------------------------------------------------------------------------

@app.route("/actividad")
def activity_view():
    entries = db.get_activity_log()
    return render_template("activity.html", entries=entries)


# ---------------------------------------------------------------------------
# PERFIL (nombre, foto, libros favoritos, copia de seguridad)
# ---------------------------------------------------------------------------

@app.route("/perfil", methods=["GET", "POST"])
def profile_view():
    if request.method == "POST":
        username = request.form.get("username", "").strip() or "guest"
        bio = request.form.get("bio", "").strip() or None

        fav_ids = []
        for i in range(1, 5):
            raw = request.form.get(f"fav_book_{i}", "").strip()
            fav_ids.append(int(raw) if raw.isdigit() else None)

        remove_photo = request.form.get("remove_photo") == "1"
        new_photo = save_profile_photo(request.files.get("photo"))
        profile = db.get_profile()
        fav_kwargs = {
            "fav_book_1": fav_ids[0], "fav_book_2": fav_ids[1],
            "fav_book_3": fav_ids[2], "fav_book_4": fav_ids[3],
        }

        if new_photo:
            delete_profile_photo_file(profile["photo_path"])
            db.update_profile(username, bio, photo_path=new_photo, keep_photo=False, **fav_kwargs)
        elif remove_photo:
            delete_profile_photo_file(profile["photo_path"])
            db.update_profile(username, bio, photo_path=None, keep_photo=False, **fav_kwargs)
        else:
            db.update_profile(username, bio, keep_photo=True, **fav_kwargs)

        db.log_activity("profile_updated", "Se actualizó el perfil.")
        flash("Perfil actualizado.", "success")
        return redirect(url_for("profile_view"))

    profile = db.get_profile()
    favorite_books = db.get_favorite_books()
    all_books = db.get_all_books(sort="title", order="asc")
    books_json = [
        {"id": b["id"], "title": b["title"], "author": b["author"] or "", "year": b["year"]}
        for b in all_books
    ]
    return render_template(
        "profile.html",
        profile=profile,
        favorite_books=favorite_books,
        books_json=books_json,
    )


@app.route("/perfil/backup/descargar")
def download_backup():
    """Descarga una copia del archivo estanteria.db tal cual está en disco."""
    if not os.path.exists(db.DB_PATH):
        abort(404)
    fecha = today_iso()
    return send_file(
        db.DB_PATH,
        as_attachment=True,
        download_name=f"sabatoxd-copia-{fecha}.db",
        mimetype="application/octet-stream",
    )


def _valid_sqlite_db(path):
    """Verificación básica de que el archivo subido es una base SQLite válida
    y tiene al menos la tabla 'books', antes de reemplazar los datos actuales."""
    try:
        conn = sqlite3.connect(path)
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        conn.close()
        return "books" in tables
    except sqlite3.Error:
        return False


@app.route("/perfil/backup/restaurar", methods=["POST"])
def restore_backup():
    confirm = request.form.get("confirm") == "1"
    file_storage = request.files.get("backup_file")

    if not confirm:
        flash("Tenés que confirmar que entendés que se reemplazarán todos tus datos actuales.", "error")
        return redirect(url_for("profile_view"))

    if not file_storage or not file_storage.filename:
        flash("Elegí un archivo de copia de seguridad (.db) para restaurar.", "error")
        return redirect(url_for("profile_view"))

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in ALLOWED_DB_EXTENSIONS:
        flash("El archivo debe ser una base de datos .db, .sqlite o .sqlite3.", "error")
        return redirect(url_for("profile_view"))

    tmp_path = os.path.join(DATA_DIR, f"_restore_tmp_{uuid.uuid4().hex}.db")
    file_storage.save(tmp_path)

    if not _valid_sqlite_db(tmp_path):
        os.remove(tmp_path)
        flash("Ese archivo no parece ser una copia de seguridad válida de Sábatoxd.", "error")
        return redirect(url_for("profile_view"))

    # Cerrar la conexión de esta request antes de pisar el archivo en disco
    db.close_db()

    # Guardar una copia de respaldo del archivo actual por las dudas
    safety_copy = os.path.join(DATA_DIR, "estanteria.antes-de-restaurar.db")
    try:
        if os.path.exists(db.DB_PATH):
            shutil.copyfile(db.DB_PATH, safety_copy)
    except OSError:
        pass

    shutil.move(tmp_path, db.DB_PATH)
    db.init_db()  # aplica migraciones a la base recién restaurada si hace falta
    db.log_activity("db_restored", "Se restauró la base de datos desde una copia de seguridad.")

    flash("Base de datos restaurada correctamente. Se guardó una copia de la anterior por las dudas.", "success")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


def _open_browser():
    webbrowser.open("http://127.0.0.1:5000")


def _run_flask():
    app.run(debug=False, port=5000, use_reloader=False)


if __name__ == "__main__":
    db.init_db()

    if getattr(sys, "frozen", False):
        # Ejecutable empaquetado: ventana nativa de escritorio con pywebview,
        # corriendo Flask en un hilo aparte.
        import webview

        threading.Thread(target=_run_flask, daemon=True).start()
        webview.create_window("Sábatoxd", "http://127.0.0.1:5000", width=1200, height=800)
        webview.start()
    else:
        # Modo desarrollo: como siempre, abre una pestaña del navegador.
        threading.Timer(1.0, _open_browser).start()
        _run_flask()
