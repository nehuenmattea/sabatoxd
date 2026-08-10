# Sábatoxd

Aplicación de escritorio para llevar un registro personal de lectura. Permite
catalogar libros, calificarlos, organizarlos en colecciones y consultar
estadísticas básicas de lo leído. Toda la información se guarda de forma
local, en un único archivo de base de datos SQLite, sin depender de servicios
externos ni de una conexión a internet para funcionar.

## Características

**Libros**
- Registro de título, autor o autores, año de publicación, cantidad de
  páginas, descripción, portada (subida por el usuario o generada
  automáticamente) y hasta cinco géneros por libro.
- Historial de lecturas: cada libro puede tener más de una lectura
  registrada, cada una con su propia fecha y calificación, lo que permite
  llevar un registro de relecturas a lo largo del tiempo.

**Autores**
- Los autores se generan automáticamente al cargar un libro. Cada autor
  cuenta con una página propia donde se listan todos los libros asociados a
  él.

**Géneros**
- Los géneros pueden crearse libremente al cargar un libro, y también
  renombrarse o eliminarse desde una sección dedicada.

**Libretas (colecciones)**
- Los libros pueden agruparse en libretas temáticas, cada una con nombre,
  color, descripción e imagen de fondo opcional.
- Un libro puede pertenecer a varias libretas a la vez.
- Cada libreta incluye además un espacio de notas de texto libre, útil para
  anotar títulos pendientes sin necesidad de cargarlos como libro todavía.

**Perfil**
- Sección de perfil con nombre de usuario, foto y hasta cuatro libros
  marcados como favoritos.

**Actividad**
- Registro cronológico de las acciones realizadas en la aplicación (altas,
  ediciones y eliminaciones de libros, libretas y géneros).

**Filtros y orden**
- La vista principal permite ordenar y filtrar los libros por calificación,
  género, autor, año de publicación, cantidad de páginas, fecha de lectura o
  búsqueda de texto libre.

**Copia de seguridad**
- Desde la sección de perfil se puede descargar la base de datos completa
  como archivo de respaldo, y restaurarla posteriormente (en la misma
  computadora o en otra). La restauración requiere confirmación explícita y
  conserva automáticamente una copia de los datos previos antes de
  reemplazarlos.

## Instalación y uso

### Ejecutable

En la sección [Releases](https://github.com/nehuenmattea/sabatoxd/releases)
del repositorio están disponibles ejecutables para Windows, macOS y Linux,
generados automáticamente. No requieren instalar Python ni ninguna
dependencia adicional.

### Desde el código fuente

Requisitos: Python 3.10 o superior.

```bash
git clone https://github.com/nehuenmattea/sabatoxd.git
cd sabatoxd
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La aplicación se abre automáticamente en `http://127.0.0.1:5000`.

## Almacenamiento de datos

Al ejecutarse desde el código fuente, los datos se guardan en la misma
carpeta del proyecto:

- `estanteria.db`: base de datos con todos los libros, autores, lecturas,
  libretas, géneros, notas, actividad y perfil.
- `static/covers/`: portadas de libros subidas por el usuario.
- `static/list_backgrounds/`: imágenes de fondo de las libretas.
- `static/profile/`: foto de perfil.

Al ejecutarse como aplicación empaquetada, estos mismos archivos se
almacenan en una carpeta independiente del programa, de modo que los datos
se conserven entre actualizaciones:

| Sistema  | Ubicación                                       |
|----------|--------------------------------------------------|
| Windows  | `%APPDATA%\Sabatoxd`                              |
| macOS    | `~/Library/Application Support/Sabatoxd`          |
| Linux    | `~/.local/share/Sabatoxd`                         |

## Estructura del proyecto

```
sabatoxd/
├── app.py              # Rutas y lógica de la aplicación (Flask)
├── database.py          # Acceso a la base de datos (SQLite)
├── build.spec            # Configuración de empaquetado (PyInstaller)
├── static/
│   ├── style.css
│   ├── app.js
│   ├── covers/
│   ├── list_backgrounds/
│   └── profile/
└── templates/             # Vistas HTML (Jinja2)
```

## Tecnologías

- **Backend:** Python, Flask
- **Base de datos:** SQLite (acceso directo, sin ORM)
- **Frontend:** HTML renderizado en el servidor (Jinja2), JavaScript sin
  frameworks
- **Empaquetado:** PyInstaller + pywebview, con compilación automática de
  ejecutables mediante GitHub Actions al publicar una nueva versión
README_EOF
Salida

# Sábatoxd

Aplicación de escritorio para llevar un registro personal de lectura. Permite
catalogar libros, calificarlos, organizarlos en colecciones y consultar
estadísticas básicas de lo leído. Toda la información se guarda de forma
local, en un único archivo de base de datos SQLite, sin depender de servicios
externos ni de una conexión a internet para funcionar.

## Características

**Libros**
- Registro de título, autor o autores, año de publicación, cantidad de
  páginas, descripción, portada (subida por el usuario o generada
  automáticamente) y hasta cinco géneros por libro.
- Historial de lecturas: cada libro puede tener más de una lectura
  registrada, cada una con su propia fecha y calificación, lo que permite
  llevar un registro de relecturas a lo largo del tiempo.

**Autores**
- Los autores se generan automáticamente al cargar un libro. Cada autor
  cuenta con una página propia donde se listan todos los libros asociados a
  él.

**Géneros**
- Los géneros pueden crearse libremente al cargar un libro, y también
  renombrarse o eliminarse desde una sección dedicada.

**Libretas (colecciones)**
- Los libros pueden agruparse en libretas temáticas, cada una con nombre,
  color, descripción e imagen de fondo opcional.
- Un libro puede pertenecer a varias libretas a la vez.
- Cada libreta incluye además un espacio de notas de texto libre, útil para
  anotar títulos pendientes sin necesidad de cargarlos como libro todavía.

**Perfil**
- Sección de perfil con nombre de usuario, foto y hasta cuatro libros
  marcados como favoritos.

**Actividad**
- Registro cronológico de las acciones realizadas en la aplicación (altas,
  ediciones y eliminaciones de libros, libretas y géneros).

**Filtros y orden**
- La vista principal permite ordenar y filtrar los libros por calificación,
  género, autor, año de publicación, cantidad de páginas, fecha de lectura o
  búsqueda de texto libre.

**Copia de seguridad**
- Desde la sección de perfil se puede descargar la base de datos completa
  como archivo de respaldo, y restaurarla posteriormente (en la misma
  computadora o en otra). La restauración requiere confirmación explícita y
  conserva automáticamente una copia de los datos previos antes de
  reemplazarlos.

## Instalación y uso

### Ejecutable

En la sección [Releases](https://github.com/nehuenmattea/sabatoxd/releases)
del repositorio están disponibles ejecutables para Windows, macOS y Linux,
generados automáticamente. No requieren instalar Python ni ninguna
dependencia adicional.

### Desde el código fuente

Requisitos: Python 3.10 o superior.

```bash
git clone https://github.com/nehuenmattea/sabatoxd.git
cd sabatoxd
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La aplicación se abre automáticamente en `http://127.0.0.1:5000`.

## Almacenamiento de datos

Al ejecutarse desde el código fuente, los datos se guardan en la misma
carpeta del proyecto:

- `estanteria.db`: base de datos con todos los libros, autores, lecturas,
  libretas, géneros, notas, actividad y perfil.
- `static/covers/`: portadas de libros subidas por el usuario.
- `static/list_backgrounds/`: imágenes de fondo de las libretas.
- `static/profile/`: foto de perfil.

Al ejecutarse como aplicación empaquetada, estos mismos archivos se
almacenan en una carpeta independiente del programa, de modo que los datos
se conserven entre actualizaciones:

| Sistema  | Ubicación                                       |
|----------|--------------------------------------------------|
| Windows  | `%APPDATA%\Sabatoxd`                              |
| macOS    | `~/Library/Application Support/Sabatoxd`          |
| Linux    | `~/.local/share/Sabatoxd`                         |

## Estructura del proyecto

```
sabatoxd/
├── app.py              # Rutas y lógica de la aplicación (Flask)
├── database.py          # Acceso a la base de datos (SQLite)
├── build.spec            # Configuración de empaquetado (PyInstaller)
├── static/
│   ├── style.css
│   ├── app.js
│   ├── covers/
│   ├── list_backgrounds/
│   └── profile/
└── templates/             # Vistas HTML (Jinja2)
```

## Tecnologías

- **Backend:** Python, Flask
- **Base de datos:** SQLite (acceso directo, sin ORM)
- **Frontend:** HTML renderizado en el servidor (Jinja2), JavaScript sin
  frameworks
- **Empaquetado:** PyInstaller + pywebview, con compilación automática de
  ejecutables mediante GitHub Actions al publicar una nueva versión