# Quick Start

Guia rapida para ejecutar la prueba tecnica en local y en Railway.

## Arquitectura

Aplicativo monolitico con FastAPI (backend y renderizado de plantillas en el mismo proceso),
PostgreSQL como base de datos, y HTML/CSS/JS.

## Requisitos

- Python 3.11 o superior
- PostgreSQL corriendo en local (o accesible por red)

## Puesta en marcha local

1. Instalar dependencias:

   ```
   pip install -r requirements.txt
   ```

2. Crear la base de datos en PostgreSQL:

   ```
   psql -U postgres (para iniciar sesion con usuario de instalacion estandar)
   
   psql -U postgres -c "CREATE DATABASE prueba_tecnica;"
   ```

3. Copiar `.env.example` a `.env` y ajustar `DATABASE_URL` con el usuario, password y puerto de tu PostgreSQL local.

4. Crea la carpeta `data/`, luego se debe colocar el archivo `PRUEBA_TECNICA.xlsx` en la carpeta creada.

5. Ejecutar el script de preparacion. Este script limpia los datos, crea las tablas, crea los usuarios de prueba y carga los datos, todo en un solo paso:

   ```
   python scripts/setup_db.py
   ```

   Es seguro ejecutarlo varias veces: si las tablas ya tienen datos o los usuarios ya existen, no los duplica.

6. Levantar el servidor:

   ```
   uvicorn app.main:app --reload
   ```

7. Abrir `http://localhost:8000`.

## Usuarios de prueba

Creados automaticamente por `scripts/setup_db.py`:

| Usuario     | Contrasena     | Rol            | Permisos                          |
|-------------|----------------|----------------|------------------------------------|
| admin       | admin123       | administrador  | consultar, crear, modificar, eliminar |
| digitador   | digitador123   | digitador      | consultar, crear                   |
| consulta    | consulta123    | consulta       | solo consultar                     |

## Roles y permisos

El control de acceso se aplica a nivel de cada endpoint del backend, no solo ocultando botones en la interfaz. Un usuario con rol `consulta` que intente invocar directamente la ruta de creacion o eliminacion recibe un error 403, independientemente de lo que vea en pantalla.

| Rol            | Consultar | Crear | Modificar | Eliminar |
|----------------|-----------|-------|-----------|----------|
| administrador  | si        | si    | si        | si       |
| digitador      | si        | si    | no        | no       |
| consulta       | si        | no    | no        | no       |

## Despliegue en Railway

1. Crear un nuevo proyecto en Railway y conectar el repositorio de GitHub.
2. Agregar un servicio de PostgreSQL desde el marketplace de Railway. Railway genera automaticamente la variable `DATABASE_URL` para ese servicio.
3. En el servicio del aplicativo web, configurar las variables de entorno:
   - `DATABASE_URL`: referenciar la del servicio de PostgreSQL (Railway permite referenciar variables de otro servicio).
   - `SECRET_KEY`: generar una clave aleatoria distinta a la del `.env.example`.
   - `SESSION_EXPIRE_MINUTES`: opcional, por defecto 120.
4. Railway detecta el `Procfile` y usa `uvicorn app.main:app --host 0.0.0.0 --port $PORT` para levantar el servicio.
5. Una vez desplegado, ejecutar `python scripts/setup_db.py` una sola vez contra la base de datos de Railway para crear las tablas, los usuarios y cargar los datos. Esto requiere subir tambien `data/PRUEBA_TECNICA.xlsx` al entorno de Railway, o ejecutar el script apuntando `DATABASE_URL` a Railway desde el equipo local.