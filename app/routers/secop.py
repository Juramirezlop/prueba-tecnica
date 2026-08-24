"""Rutas CRUD para la hoja SECOP. Llave de negocio: referencia."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import requerir_permiso
from app.database import get_db
from app.models import Secop

router = APIRouter(prefix="/secop", tags=["secop"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def listar(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("consultar")),
):
    query = db.query(Secop)
    if q:
        query = query.filter(Secop.referencia.ilike(f"%{q}%"))
    registros = query.order_by(Secop.referencia).all()
    return templates.TemplateResponse(
        "secop_list.html",
        {"request": request, "registros": registros, "usuario": usuario, "q": q},
    )


@router.get("/nuevo", response_class=HTMLResponse)
def form_crear(request: Request, usuario=Depends(requerir_permiso("crear"))):
    return templates.TemplateResponse(
        "secop_form.html",
        {"request": request, "usuario": usuario, "registro": None, "modo": "crear"},
    )


@router.post("/nuevo")
def crear(
    request: Request,
    referencia: str = Form(...),
    pais: str = Form(""),
    entidad_estatal: str = Form(""),
    descripcion: str = Form(""),
    fase_actual: str = Form(""),
    fecha_publicacion: str = Form(""),
    fecha_presentacion_ofertas: str = Form(""),
    url_detalle: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("crear")),
):
    nuevo = Secop(
        referencia=referencia.strip(),
        pais=pais,
        entidad_estatal=entidad_estatal,
        descripcion=descripcion,
        fase_actual=fase_actual,
        fecha_publicacion=fecha_publicacion,
        fecha_presentacion_ofertas=fecha_presentacion_ofertas,
        url_detalle=url_detalle,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/secop", status_code=303)


@router.get("/{referencia}/editar", response_class=HTMLResponse)
def form_editar(
    referencia: str,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("modificar")),
):
    registro = db.query(Secop).filter(Secop.referencia == referencia).first()
    return templates.TemplateResponse(
        "secop_form.html",
        {"request": request, "usuario": usuario, "registro": registro, "modo": "editar"},
    )


@router.post("/{referencia}/editar")
def editar(
    referencia: str,
    pais: str = Form(""),
    entidad_estatal: str = Form(""),
    descripcion: str = Form(""),
    fase_actual: str = Form(""),
    fecha_publicacion: str = Form(""),
    fecha_presentacion_ofertas: str = Form(""),
    url_detalle: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("modificar")),
):
    registro = db.query(Secop).filter(Secop.referencia == referencia).first()
    if registro:
        registro.pais = pais
        registro.entidad_estatal = entidad_estatal
        registro.descripcion = descripcion
        registro.fase_actual = fase_actual
        registro.fecha_publicacion = fecha_publicacion
        registro.fecha_presentacion_ofertas = fecha_presentacion_ofertas
        registro.url_detalle = url_detalle
        db.commit()
    return RedirectResponse(url="/secop", status_code=303)


@router.post("/{referencia}/eliminar")
def eliminar(
    referencia: str,
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("eliminar")),
):
    registro = db.query(Secop).filter(Secop.referencia == referencia).first()
    if registro:
        db.delete(registro)
        db.commit()
    return RedirectResponse(url="/secop", status_code=303)
