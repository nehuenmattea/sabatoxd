# Mi Estantería 📖

Aplicación personal y 100% local para registrar los libros que leés, calificarlos
y organizarlos en libretas (listas), inspirada en Letterboxd/Serializd pero para libros.

Toda la información se guarda en un archivo SQLite (`estanteria.db`) en tu propia
computadora. No se envía nada a internet ni requiere cuenta de usuario.

## Descarga directa (sin instalar nada)

Si solo querés **usar** la app, sin tocar código:

1. Andá a la sección [Releases](../../releases) de este repositorio.
2. Descargá el archivo que corresponda a tu sistema operativo (`Sabatoxd-Windows.exe`,
   `Sabatoxd-Mac` o `Sabatoxd-Linux`).
3. Abrilo con doble clic. Se va a abrir una ventana de la app; no hace falta
   terminal ni instalar Python.
   - En Windows, si aparece un aviso de "Windows protegió tu PC" (SmartScreen),
     tocá "Más información" → "Ejecutar de todas formas". Pasa porque el
     ejecutable no está firmado digitalmente, no porque tenga algo malo.
   - En Mac, si dice que no se puede abrir porque es de un desarrollador no
     identificado, hacé clic derecho sobre el archivo → "Abrir" → "Abrir" (solo
     hace falta la primera vez).
4. Tus libros y libretas se guardan en tu computadora, en una carpeta propia de
   la app (no adentro del ejecutable), así que no se pierden si lo actualizás
   más adelante.

## Para desarrolladores: correrla desde el código

### Requisitos

- Python 3.9 o superior instalado en tu computadora.

### Instalación (solo la primera vez)

Abrí una terminal en esta carpeta y ejecutá:

```bash
pip install -r requirements.txt
```

### Cómo usarla

Cada vez que quieras abrir la app:

```bash
python app.py
```

Esto va a abrir automáticamente `http://127.0.0.1:5000` en tu navegador. Si no se
abre solo, entrá manualmente a esa dirección.

Para cerrar la app, volvé a la terminal y presioná `Ctrl + C`.

### Generar el ejecutable vos mismo

Los ejecutables de la sección "Releases" se generan automáticamente con GitHub
Actions (ver `.github/workflows/build.yml`) cada vez que se publica un tag
`vX.Y.Z`. Si querés generarlo a mano en tu computadora:

```bash
pip install -r requirements-build.txt
pyinstaller build.spec --noconfirm
```

El ejecutable queda en `dist/`. Ojo: PyInstaller genera un binario para el
sistema operativo en el que lo corrés (si lo compilás en Windows, te da un
`.exe`; en Mac, el binario de Mac). Por eso el workflow de GitHub Actions
compila en los tres sistemas en paralelo.

## Qué incluye

- **Registrar libros**: título, autor, año de publicación, fecha de lectura (no permite
  fechas futuras), calificación de 1 a 5 estrellas **con medias estrellas**, hasta 5
  géneros y una portada opcional (si no subís una, se genera una automáticamente).
- **Géneros**: hay 17 precargados (Poesía, Terror, Ciencia ficción, Fantasía, etc.) y
  podés agregar los que quieras escribiéndolos en el campo "Agregar género nuevo".
  Cada libro admite hasta 5.
- **Libretas (listas)**: creá tantas como quieras, con un color básico a elección
  (rojo, naranja, amarillo, verde, azul, morado, rosa, gris), una descripción y,
  opcionalmente, una imagen de fondo (estilo Letterboxd) que se muestra tanto en la
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

Si corrés la app desde el código (`python app.py`), todo se guarda en esta misma
carpeta:

- `estanteria.db`: la base de datos con todos tus libros, libretas y géneros.
- `static/covers/`: las imágenes de portada que subas.
- `static/list_backgrounds/`: las imágenes de fondo de tus libretas.

Si usás el **ejecutable** descargado de Releases, esos mismos archivos se
guardan en una carpeta propia fuera del programa, para que sobrevivan a futuras
actualizaciones:

- Windows: `%APPDATA%\Sabatoxd`
- Mac: `~/Library/Application Support/Sabatoxd`
- Linux: `~/.local/share/Sabatoxd`

Para hacer una copia de seguridad, simplemente copiá esa carpeta a otro lugar
(por ejemplo, a un pendrive o a Google Drive). Para restaurarla, volvé a
colocarla en el mismo lugar antes de abrir la app.

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

## Preguntas frecuentes

**¿Puedo tener varios lectores/usuarios?**
No, está pensada para un único usuario en una sola computadora.

**¿Funciona sin internet?**
Sí. Solo intenta cargar las tipografías (Fraunces/Inter) desde Google Fonts; si no
hay conexión, usa automáticamente tipografías del sistema y se ve igual de bien.

**¿Cómo cambio el puerto si el 5000 está ocupado?**
Editá la última línea de `app.py` (`app.run(debug=False, port=5000)`) y cambiá el
número de puerto.


