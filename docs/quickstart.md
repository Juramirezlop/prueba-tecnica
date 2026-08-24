# Quick Start

Guia rapida para poner en marcha el aplicativo de SECOP y CC2026 en local
y en Railway.

## Arquitectura

Aplicativo monolitico con FastAPI (backend y renderizado de plantillas en
el mismo proceso), PostgreSQL como base de datos, y HTML/CSS/JS sin
framework de frontend.

```
app/
  main.py            punto de entrada, home, login, logout
  database.py         conexion a PostgreSQL con SQLAlchemy
  models.py            tablas: usuarios, secop, cc2026
  auth.py               sesion por JWT en cookie, permisos por rol
  routers/
    secop.py            CRUD de SECOP
    cc2026.py            CRUD de CC2026
  templates/            HTML con Jinja2
  static/                CSS y JS
scripts/
  setup_db.py          limpieza del Excel + creacion de tablas + carga de datos
data/
  PRUEBA_TECNICA.xlsx   archivo original (colocar aqui, no se versiona)
  secop_clean.csv         salida de la limpieza (se genera al ejecutar el script)
  cc2026_clean.csv         salida de la limpieza (se genera al ejecutar el script)
```

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
   psql -U postgres -c "CREATE DATABASE prueba_tecnica;"
   ```

3. Copiar `.env.example` a `.env` y ajustar `DATABASE_URL` con el usuario,
   password y puerto de tu PostgreSQL local.

4. Colocar el archivo `PRUEBA_TECNICA.xlsx` (el original de la prueba) en
   la carpeta `data/`.

5. Ejecutar el script de preparacion. Este script limpia los datos, crea
   las tablas, crea los usuarios de prueba y carga los datos, todo en un
   solo paso:

   ```
   python scripts/setup_db.py
   ```

   Es seguro ejecutarlo varias veces: si las tablas ya tienen datos o los
   usuarios ya existen, no los duplica.

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

Cambiar estas contrasenas antes de exponer el servicio publicamente
(editar la lista `USUARIOS_INICIALES` en `scripts/setup_db.py` o
actualizar los usuarios directamente en la base de datos).

## Proceso de depuracion de datos

El script `scripts/setup_db.py` aplica, sobre cada hoja del Excel
original, los siguientes pasos en orden:

1. Elimina columnas donde mas del 95% de las filas estan vacias. En la
   hoja SECOP esto descarta 34 de las 46 columnas originales (metadata de
   la exportacion sin uso real: iconos, banderas de pais, columnas sin
   dato en casi ningun proceso).
2. Elimina filas sin valor en la columna llave (`Referencia` en SECOP,
   `Radicacion` en CC2026).
3. En SECOP especificamente: elimina filas de paginacion. El archivo
   original tiene, cada aproximadamente 30 registros, una fila donde
   todas las columnas repiten el mismo numero corto (1, 2, 3, ...) y no
   tienen URL de detalle — es un artefacto del proceso de scraping
   original de la pagina de SECOP, no un proceso de contratacion real.
   Se identifican y eliminan 32 filas de este tipo.
4. Elimina duplicados por llave, conservando el primer registro.
5. Normaliza los nombres de columna a snake_case.
6. Selecciona el subconjunto final de columnas con informacion relevante
   para el aplicativo (se descartan columnas que sobreviven al filtro de
   nulos pero no aportan informacion util, como texto constante o iconos).

Resultado tipico sobre el archivo de la prueba:

- SECOP: 190 filas originales -> 158 filas limpias, de 46 a 8 columnas.
- CC2026: 548 filas originales -> 548 filas limpias, de 13 a 9 columnas.

El resultado se guarda en `data/secop_clean.csv` y `data/cc2026_clean.csv`
como evidencia del proceso, ademas de cargarse directamente a la base de
datos.

## Roles y permisos

El control de acceso se aplica a nivel de cada endpoint del backend, no
solo ocultando botones en la interfaz. Un usuario con rol `consulta` que
intente invocar directamente la ruta de creacion o eliminacion recibe un
error 403, independientemente de lo que vea en pantalla.

| Rol            | Consultar | Crear | Modificar | Eliminar |
|----------------|-----------|-------|-----------|----------|
| administrador  | si        | si    | si        | si       |
| digitador      | si        | si    | no        | no       |
| consulta       | si        | no    | no        | no       |

### Limitacion conocida: bloqueo de copia para el rol Consulta

El requerimiento pide que el rol Consulta no pueda copiar texto en
pantalla. Esto se implementa en `app/static/app.js` mediante JavaScript
(se bloquea el evento de copiar y el menu contextual). Es una restriccion
de interfaz, no una medida de seguridad: un usuario con conocimientos
tecnicos puede acceder al contenido igualmente desde las herramientas de
desarrollador del navegador o consultando la respuesta HTTP directamente.
Se documenta esta limitacion de forma explicita para no dar una falsa
sensacion de seguridad.

## Despliegue en Railway

1. Crear un nuevo proyecto en Railway y conectar el repositorio de
   GitHub.
2. Agregar un servicio de PostgreSQL desde el marketplace de Railway.
   Railway genera automaticamente la variable `DATABASE_URL` para ese
   servicio.
3. En el servicio del aplicativo web, configurar las variables de
   entorno:
   - `DATABASE_URL`: referenciar la del servicio de PostgreSQL (Railway
     permite referenciar variables de otro servicio).
   - `SECRET_KEY`: generar una clave aleatoria distinta a la del
     `.env.example`.
   - `SESSION_EXPIRE_MINUTES`: opcional, por defecto 120.
4. Railway detecta el `Procfile` y usa `uvicorn app.main:app --host
   0.0.0.0 --port $PORT` para levantar el servicio.
5. Una vez desplegado, ejecutar `python scripts/setup_db.py` una sola vez
   contra la base de datos de Railway (por ejemplo desde la consola o CLI
   de Railway) para crear las tablas, los usuarios y cargar los datos.
   Esto requiere subir tambien `data/PRUEBA_TECNICA.xlsx` al entorno de
   Railway, o ejecutar el script apuntando `DATABASE_URL` a Railway desde
   el equipo local.

## Notas para la sustentacion tecnica

- El diseno es intencionalmente monolitico: un solo servicio, sin
  microservicios ni colas, porque el alcance del proyecto no lo justifica.
- PostgreSQL se eligio sobre MySQL (que el enunciado sugiere como opcion,
  no como requisito) por experiencia previa del equipo con ese motor y
  por su soporte nativo en Railway.
- La limpieza de datos es reproducible y esta separada logicamente de la
  carga (aunque ambas corren en un solo comando): el codigo de limpieza
  puede revisarse y ejecutarse de forma aislada llamando directamente a
  las funciones `clean_secop` y `clean_cc2026` de `scripts/setup_db.py`.
