# Sábatoxd

Una estantería de libros que corre en tu propia computadora. Sin cuentas, sin
nube, sin que nadie más vea qué estás leyendo. La base de datos es un único
archivo `.db` que vive en tu disco.

La empecé porque quería algo tipo Goodreads o Letterboxd pero para libros,
liviano, y que no le mande mis datos de lectura a nadie. Terminó siendo un
Flask + SQLite bastante completo: autores múltiples, relecturas con
calificaciones separadas, libretas para organizar los libros en colecciones,
y un empaquetado a ejecutable de escritorio para no depender de tener Python
instalado.

## Qué hace

- **Libros**: título, uno o más autores, año, páginas, descripción, portada
  (subida o generada automáticamente) y hasta 5 géneros.
- **Relecturas**: cada vez que releés un libro podés registrar una nueva
  fecha y calificación sin perder el historial anterior. La ficha del libro
  muestra todas las lecturas; la más reciente es la que se usa para ordenar
  y filtrar en la vista general.
- **Autores**: se crean solos al cargar un libro. Tocando un autor ves todos
  sus libros sin tener que buscar nada.
- **Libretas**: colecciones de libros con color, descripción e imagen de
  fondo propia. Podés agregar libros ya cargados con un buscador o con un
  selector visual (tocás uno y se atenúa para marcar que ya está agregado).
  También tienen un bloc de notas de texto libre para anotar cosas como
  "para leer" sin necesidad de cargar el libro todavía.
- **Géneros**: los que vienen precargados se pueden renombrar o borrar como
  cualquier otro.
- **Perfil**: nombre de usuario, foto y hasta 4 libros favoritos, al estilo
  Letterboxd. Por defecto es "guest" y sin foto.
- **Actividad**: un registro cronológico de qué se agregó, editó o borró.
- **Copia de seguridad**: descargar y restaurar la base de datos completa
  desde el perfil, para llevarte tus datos a otra computadora o simplemente
  tener un respaldo. Al restaurar pide confirmación explícita y guarda una
  copia de lo anterior por las dudas.
- Filtros y orden por calificación (con medias estrellas), género, autor,
  año, páginas, fecha de lectura y búsqueda de texto.

## Cómo se usa

### Descargando el ejecutable

Es la forma más simple si no querés tocar código. En [Releases][releases] hay
un ejecutable para Windows, Mac y Linux — se compilan solos con GitHub
Actions cada vez que se publica una versión nueva. Lo abrís y listo, no hace
falta instalar Python ni nada.

[releases]: https://github.com/nehuenmattea/sabatoxd/releases

### Corriéndolo desde el código

```bash
git clone https://github.com/nehuenmattea/sabatoxd.git
cd sabatoxd
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Se abre solo en `http://127.0.0.1:5000`.

## Dónde vive tu información

- Corriendo desde el código: todo queda en la misma carpeta del proyecto
  (`estanteria.db`, `static/covers/`, `static/list_backgrounds/`,
  `static/profile/`).
- Corriendo el ejecutable: en una carpeta aparte fuera del programa, para que
  sobreviva a las actualizaciones (`%APPDATA%\Sabatoxd` en Windows,
  `~/Library/Application Support/Sabatoxd` en Mac,
  `~/.local/share/Sabatoxd` en Linux).

Para respaldar o mover tus datos a otra computadora, lo más simple es
**Perfil → Copia de seguridad**, que descarga un único archivo `.db` con
todo. También podés copiar esa carpeta a mano si preferís.

## Cómo está armado

```
sabatoxd/
├── app.py              # rutas Flask y lógica de la aplicación
├── database.py          # todo el acceso a SQLite, sin ORM
├── build.spec           # empaquetado a ejecutable con PyInstaller
├── static/
│   ├── style.css
│   ├── app.js            # JS vanilla, sin frameworks
│   ├── covers/
│   ├── list_backgrounds/
│   └── profile/
└── templates/            # Jinja2, server-side rendering
```

Decisiones a propósito:

- **Sin ORM.** `database.py` usa `sqlite3` directo con SQL escrito a mano.
  Para el tamaño de esta app un ORM agrega más capas de las que resuelve.
- **Sin frameworks de frontend.** Las páginas son HTML renderizado en el
  servidor; el JS que hay es solo para las partes que necesitan
  interactividad puntual (el selector visual de libros, los buscadores).
- **Migraciones caseras.** `init_db()` corre en cada arranque y aplica los
  cambios de esquema que falten sin borrar nada existente. No hay un
  sistema de migraciones formal (tipo Alembic) porque para una app de un
  solo usuario local no vale la pena la complejidad extra.
- **El ejecutable envuelve el mismo Flask.** El build con PyInstaller usa
  [pywebview](https://pywebview.flowrl.com/) para mostrar una ventana nativa
  en vez de abrir el navegador, pero por debajo sigue siendo la misma app
  Flask corriendo en un hilo local.

## Stack

Python · Flask · SQLite · Jinja2 · JavaScript vanilla · PyInstaller

## Estado

Uso personal, en desarrollo activo cuando me surge una idea o encuentro algo
que me gustaría que hiciera distinto. Si algo se rompe o tenés una sugerencia,
abrí un issue.
