"""
Sábatoxd
Aplicación local para registrar libros, calificarlos y organizarlos en listas.
Ejecutar con: python app.py
Luego abrir: http://127.0.0.1:5000
"""

import os
import uuid
import webbrowser
import threading
from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from werkzeug.utils import secure_filename

import database as db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COVERS_FOLDER = os.path.join(BASE_DIR, "static", "covers")
BACKGROUNDS_FOLDER = os.path.join(BASE_DIR, "static", "list_backgrounds")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

os.makedirs(COVERS_FOLDER, exist_ok=True)
os.makedirs(BACKGROUNDS_FOLDER, exist_ok=True)

app = Flask(__name__)
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


# Filtros / globals de Jinja
app.jinja_env.globals["placeholder_color"] = placeholder_color
app.jinja_env.globals["list_colors"] = db.LIST_COLORS
app.jinja_env.globals["color_hex"] = lambda name: db.COLOR_HEX_MAP.get(name, "#707885")
app.jinja_env.globals["rating_options"] = db.RATING_OPTIONS
app.jinja_env.globals["max_genres"] = db.MAX_GENRES_PER_BOOK


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
    """Extrae y normaliza los datos del formulario de libro.
    Devuelve (data, error) — error es un mensaje si algo no es válido."""
    title = form.get("title", "").strip()
    author = form.get("author", "").strip()
    year = form.get("year", "").strip()
    pages = form.get("pages", "").strip()
    date_read = form.get("date_read", "").strip()
    rating_raw = form.get("rating", "0").strip()

    error = None

    if date_read and date_read > today_iso():
        error = "La fecha de lectura no puede ser posterior al día de hoy."

    try:
        rating = float(rating_raw) if rating_raw else 0.0
        # redondear a la media estrella más cercana y limitar a [0, 5]
        rating = round(rating * 2) / 2
        rating = max(0.0, min(5.0, rating))
    except ValueError:
        rating = 0.0

    return {
        "title": title,
        "author": author or None,
        "year": int(year) if year.isdigit() else None,
        "pages": int(pages) if pages.isdigit() else None,
        "date_read": date_read or None,
        "rating": rating,
    }, error


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

    genre_ids = list(dict.fromkeys(genre_ids))  
    warning = None
    if len(genre_ids) > db.MAX_GENRES_PER_BOOK:
        warning = f"Un libro puede tener hasta {db.MAX_GENRES_PER_BOOK} géneros; se guardaron los primeros {db.MAX_GENRES_PER_BOOK}."
        genre_ids = genre_ids[: db.MAX_GENRES_PER_BOOK]

    return genre_ids, warning


# ---------------------------------------------------------------------------
# INICIO / LIBROS
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    sort = request.args.get("sort", "added")
    order = request.args.get("order", "desc")
    rating_filter = request.args.get("rating", "")
    genre_filter = request.args.get("genre", "")
    q = request.args.get("q", "").strip()

    books = db.get_all_books(
        sort=sort, order=order, rating_filter=rating_filter,
        search=q, genre_filter=genre_filter,
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
        q=q,
        stats=stats,
        genres=genres,
    )


@app.route("/libro/nuevo", methods=["GET", "POST"])
def new_book():
    if request.method == "POST":
        data, error = parse_book_form(request.form)
        genre_ids, genre_warning = parse_genres_form(request.form)

        if not data["title"]:
            error = "El título es obligatorio."

        if error:
            flash(error, "error")
            return render_template(
                "book_form.html", book=None, form_data=data,
                genres=db.get_all_genres(), selected_genre_ids=genre_ids, today=today_iso(),
            )

        if genre_warning:
            flash(genre_warning, "error")

        cover_filename = save_cover(request.files.get("cover"))
        book_id = db.create_book(
            data["title"], data["author"], data["year"], data["pages"],
            data["date_read"], data["rating"], cover_filename,
        )
        db.set_book_genres(book_id, genre_ids)

        # Si se abrió el formulario desde una lista específica, agregarlo ahí
        add_to_list = request.args.get("list_id") or request.form.get("list_id")
        if add_to_list:
            db.add_book_to_list(int(add_to_list), book_id)
            return redirect(url_for("list_detail", list_id=add_to_list))

        flash(f'"{data["title"]}" se agregó a tu estantería.', "success")
        return redirect(url_for("book_detail", book_id=book_id))

    return render_template(
        "book_form.html", book=None, form_data=None,
        genres=db.get_all_genres(), selected_genre_ids=[], today=today_iso(),
    )


@app.route("/libro/<int:book_id>")
def book_detail(book_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)
    lists = db.get_lists_for_book(book_id)
    genres = db.get_genres_for_book(book_id)
    return render_template("book_detail.html", book=book, lists=lists, genres=genres)


@app.route("/libro/<int:book_id>/editar", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.get_book(book_id)
    if not book:
        abort(404)

    if request.method == "POST":
        data, error = parse_book_form(request.form)
        genre_ids, genre_warning = parse_genres_form(request.form)

        if not data["title"]:
            error = "El título es obligatorio."

        if error:
            flash(error, "error")
            return render_template(
                "book_form.html", book=book, form_data=data,
                genres=db.get_all_genres(), selected_genre_ids=genre_ids, today=today_iso(),
            )

        if genre_warning:
            flash(genre_warning, "error")

        remove_cover = request.form.get("remove_cover") == "1"
        new_cover = save_cover(request.files.get("cover"))

        if new_cover:
            delete_cover_file(book["cover_path"])
            db.update_book(book_id, data["title"], data["author"], data["year"],
                            data["pages"], data["date_read"], data["rating"],
                            cover_path=new_cover, keep_cover=False)
        elif remove_cover:
            delete_cover_file(book["cover_path"])
            db.update_book(book_id, data["title"], data["author"], data["year"],
                            data["pages"], data["date_read"], data["rating"],
                            cover_path=None, keep_cover=False)
        else:
            db.update_book(book_id, data["title"], data["author"], data["year"],
                            data["pages"], data["date_read"], data["rating"],
                            keep_cover=True)

        db.set_book_genres(book_id, genre_ids)

        flash(f'"{data["title"]}" se actualizó.', "success")
        return redirect(url_for("book_detail", book_id=book_id))

    current_genre_ids = [g["id"] for g in db.get_genres_for_book(book_id)]
    return render_template(
        "book_form.html", book=book, form_data=None,
        genres=db.get_all_genres(), selected_genre_ids=current_genre_ids, today=today_iso(),
    )


@app.route("/libro/<int:book_id>/borrar", methods=["POST"])
def delete_book(book_id):
    book = db.get_book(book_id)
    if book:
        delete_cover_file(book["cover_path"])
        db.delete_book(book_id)
        flash(f'"{book["title"]}" se eliminó de tu estantería.', "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# LISTAS
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
    available_books = db.get_books_not_in_list(list_id)
    available_books_json = [
        {
            "id": b["id"],
            "title": b["title"],
            "author": b["author"] or "",
            "year": b["year"],
        }
        for b in available_books
    ]
    return render_template(
        "list_detail.html",
        list=lst,
        books=books,
        sort=sort,
        order=order,
        available_books_json=available_books_json,
        has_available=len(available_books) > 0,
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

        flash("Libreta actualizada.", "success")
        return redirect(url_for("list_detail", list_id=list_id))
    return render_template("list_form.html", list=lst)


@app.route("/listas/<int:list_id>/borrar", methods=["POST"])
def delete_list(list_id):
    lst = db.get_list(list_id)
    if lst:
        delete_background_file(lst["background_path"])
        db.delete_list(list_id)
        flash(f'Libreta "{lst["name"]}" eliminada (los libros no se borraron).', "success")
    return redirect(url_for("lists_view"))


@app.route("/listas/<int:list_id>/agregar", methods=["POST"])
def add_book_to_list(list_id):
    book_id = request.form.get("book_id", "")
    if book_id.isdigit():
        db.add_book_to_list(list_id, int(book_id))
        flash("Libro agregado a la lista.", "success")
    else:
        flash("Elegí un libro de la lista de resultados antes de agregar.", "error")
    return redirect(url_for("list_detail", list_id=list_id))


@app.route("/listas/<int:list_id>/quitar/<int:book_id>", methods=["POST"])
def remove_book_from_list(list_id, book_id):
    db.remove_book_from_list(list_id, book_id)
    flash("Libro quitado de la lista.", "success")
    return redirect(url_for("list_detail", list_id=list_id))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


def _open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    db.init_db()
    threading.Timer(1.0, _open_browser).start()
    app.run(debug=False, port=5000)
