"""Punto de entrada de la aplicacion.

Define el home, el login/logout, el manejo de errores de autenticacion,
y monta los routers de SECOP y CC2026.
"""

from fastapi import Depends, FastAPI, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.auth import crear_token_sesion, obtener_usuario_actual, verificar_password
from app.database import get_db
from app.models import Usuario
from app.routers import cc2026, secop

app = FastAPI(title="Prueba Tecnica - SECOP y CC2026")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(secop.router)
app.include_router(cc2026.router)


@app.exception_handler(HTTPException)
async def manejar_error_http(request: Request, exc: HTTPException):
    """Redirige a /login cuando falta sesion; muestra un 403 simple si el
    rol no tiene permiso para la accion solicitada."""
    if exc.status_code == HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url=f"/login?next={request.url.path}", status_code=303)
    if exc.status_code == HTTP_403_FORBIDDEN:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "mensaje": exc.detail, "codigo": 403},
            status_code=403,
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "mensaje": exc.detail, "codigo": exc.status_code},
        status_code=exc.status_code,
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    usuario = obtener_usuario_actual(request, db)
    return templates.TemplateResponse("home.html", {"request": request, "usuario": usuario})


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/"):
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "next": next})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario or not verificar_password(password, usuario.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario o contrasena incorrectos.", "next": next},
            status_code=401,
        )

    token = crear_token_sesion(usuario.username, usuario.rol)
    destino = next if next and next.startswith("/") else "/"
    respuesta = RedirectResponse(url=destino, status_code=303)
    respuesta.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 2,
    )
    return respuesta


@app.get("/logout")
def logout():
    respuesta = RedirectResponse(url="/", status_code=303)
    respuesta.delete_cookie("session_token")
    return respuesta
