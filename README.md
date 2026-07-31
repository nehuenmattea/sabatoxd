# Sábatoxd

Aplicación personal y 100% local para registrar los libros que leés, calificarlos
y organizarlos en libretas (listas), inspirada en Letterboxd/Serializd pero para libros.

Toda la información se guarda en un archivo SQLite (`estanteria.db`) en tu propia
computadora. No se envía nada a internet ni requiere cuenta de usuario.

## Requisitos

- Python 3.9 o superior instalado en tu computadora.

## Instalación (solo la primera vez)

Abrí una terminal en esta carpeta y ejecutá:

```bash
pip install -r requirements.txt
```

## Cómo usarla

Cada vez que quieras abrir la app:

```bash
python app.py
```

Esto va a abrir automáticamente `http://127.0.0.1:5000` en tu navegador. Si no se
abre solo, entrá manualmente a esa dirección.

Para cerrar la app, volvé a la terminal y presioná `Ctrl + C`.

## Qué incluye

- **Registrar libros**: título, autor, año de publicación, fecha de lectura (no permite
  fechas futuras), calificación de 1 a 5 estrellas **con medias estrellas**, hasta 5
  géneros y una portada opcional (si no subís una, se genera una automáticamente).
- **Géneros**: hay 17 precargados (Poesía, Terror, Ciencia ficción, Fantasía, etc.) y
  podés agregar los que quieras escribiéndolos en el campo "Agregar género nuevo".
  Cada libro admite hasta 5.
- **Libretas (listas)**: creá tantas como quieras, con un color básico a elección
  (rojo, naranja, amarillo, verde, azul, morado, rosa, gris), una descripción y,
  opcionalmente, una imagen de fondo que se muestra tanto en la
  tarjeta de la libreta como en su encabezado.
- **Reutilizar libros entre libretas**: dentro de cada libreta hay un buscador que
  te deja agregar un libro ya cargado sin tener que volver a escribir sus datos.
  Un mismo libro puede estar en varias libretas a la vez.
- **Vista general de todos los libros** con filtros y orden:
  - Por calificación, incluyendo medias estrellas (4.5, 3.5, etc.) y "sin calificar".
  - Por género.
  - Alfabético por título o autor (A-Z / Z-A).
  - Por año de publicación (más viejo → más nuevo o al revés).
  - Por cantidad de páginas.
  - Por fecha de lectura.
  - Búsqueda de texto libre por título/autor.
- Editar y eliminar libros o libretas en cualquier momento (eliminar una libreta
  **no** borra los libros, solo la agrupación).
- Si ya tenías una versión anterior de la app con datos cargados, no hay que hacer
  nada especial: al iniciar, la app actualiza la base de datos automáticamente sin
  borrar nada.

## Dónde queda guardada tu información

- `estanteria.db`: la base de datos con todos tus libros, libretas y géneros.
- `static/covers/`: las imágenes de portada que subas.
- `static/list_backgrounds/`: las imágenes de fondo de tus libretas.

Para hacer una copia de seguridad, simplemente copiá esos elementos a otro
lugar (por ejemplo, a un pendrive o a Google Drive). Para restaurarla, volvé a
colocarlos en esta misma carpeta antes de ejecutar `python app.py`.

## Estructura del proyecto

```
book_tracker/
├── app.py              # Rutas y lógica de la aplicación (Flask)
├── database.py          # Acceso a la base de datos SQLite
├── requirements.txt
├── static/
│   ├── style.css
│   ├── app.js
│   └── covers/           # Portadas subidas por vos
└── templates/            # Páginas HTML
```

## Posibles preguntas

**¿Puedo tener varios lectores/usuarios?**
No, está pensada para un único usuario en una sola computadora.

**¿Funciona sin internet?**
Sí. Solo intenta cargar las tipografías (Fraunces/Inter) desde Google Fonts; si no
hay conexión, usa automáticamente tipografías del sistema y se ve igual de bien.

**¿Cómo cambio el puerto si el 5000 está ocupado?**
Editá la última línea de `app.py` (`app.run(debug=False, port=5000)`) y cambiá el
número de puerto.