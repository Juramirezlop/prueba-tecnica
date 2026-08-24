# Prueba tecnica — SECOP y CC2026

Aplicativo web para consultar y administrar los registros de dos fuentes de datos

## Stack

FastAPI (backend y renderizado de HTML) + PostgreSQL + SQLAlchemy + Jinja2 + HTML/CSS/JS. 
Arquitectura monolitica, pensada para el alcance de esta prueba.

## Contenido

- `app/`: codigo de la aplicacion (rutas, modelos, autenticacion,
  plantillas, estaticos).
- `scripts/setup_db.py`: limpia el Excel original, crea las tablas, crea
  los usuarios de prueba y carga los datos. Un solo comando.
- `docs/quickstart.md`: guia de instalacion local, despliegue en Railway.

## Inicio rapido

Ver [`docs/quickstart.md`](docs/quickstart.md) para la guia completa.
En resumen:

```
pip install -r requirements.txt
cp .env.example .env   # ajustar DATABASE_URL
# colocar PRUEBA_TECNICA.xlsx en data/
python scripts/setup_db.py
uvicorn app.main:app --reload
```