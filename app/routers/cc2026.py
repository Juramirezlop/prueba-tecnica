"""Rutas CRUD para la hoja CC2026. Llave de negocio: radicacion."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.auth import requerir_permiso
from app.database import get_db
from app.models import CC2026
from app.pagination import PAGE_SIZE, calcular_total_paginas, rango_paginas

router = APIRouter(prefix="/cc2026", tags=["cc2026"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
def listar(
    request: Request,
    q: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("consultar")),
):
    query = db.query(CC2026)
    if q:
        query = query.filter(CC2026.radicacion.ilike(f"%{q}%"))

    total_registros = query.count()
    total_paginas = calcular_total_paginas(total_registros)
    page = max(1, min(page, total_paginas))

    registros = (
        query.order_by(CC2026.radicacion)
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
        .all()
    )

    return templates.TemplateResponse(
        "cc2026_list.html",
        {
            "request": request,
            "registros": registros,
            "usuario": usuario,
            "q": q,
            "page": page,
            "total_paginas": total_paginas,
            "paginas": rango_paginas(page, total_paginas),
            "total_registros": total_registros,
        },
    )

@router.get("/nuevo", response_class=HTMLResponse)
def form_crear(request: Request, usuario=Depends(requerir_permiso("crear"))):
    return templates.TemplateResponse(
        "cc2026_form.html",
        {"request": request, "usuario": usuario, "registro": None, "modo": "crear"},
    )

@router.post("/nuevo")
def crear(
    request: Request,
    radicacion: str = Form(...),
    numero: str = Form(""),
    ponente: str = Form(""),
    norma_demandada: str = Form(""),
    demandante: str = Form(""),
    fecha: str = Form(""),
    url_proceso: str = Form(""),
    url_demanda: str = Form(""),
    capture_date: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("crear")),
):
    nuevo = CC2026(
        radicacion=radicacion.strip(),
        numero=numero,
        ponente=ponente,
        norma_demandada=norma_demandada,
        demandante=demandante,
        fecha=fecha,
        url_proceso=url_proceso,
        url_demanda=url_demanda,
        capture_date=capture_date,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/cc2026", status_code=303)

@router.get("/{radicacion}/editar", response_class=HTMLResponse)
def form_editar(
    radicacion: str,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("modificar")),
):
    registro = db.query(CC2026).filter(CC2026.radicacion == radicacion).first()
    return templates.TemplateResponse(
        "cc2026_form.html",
        {"request": request, "usuario": usuario, "registro": registro, "modo": "editar"},
    )

@router.post("/{radicacion}/editar")
def editar(
    radicacion: str,
    numero: str = Form(""),
    ponente: str = Form(""),
    norma_demandada: str = Form(""),
    demandante: str = Form(""),
    fecha: str = Form(""),
    url_proceso: str = Form(""),
    url_demanda: str = Form(""),
    capture_date: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("modificar")),
):
    registro = db.query(CC2026).filter(CC2026.radicacion == radicacion).first()
    if registro:
        registro.numero = numero
        registro.ponente = ponente
        registro.norma_demandada = norma_demandada
        registro.demandante = demandante
        registro.fecha = fecha
        registro.url_proceso = url_proceso
        registro.url_demanda = url_demanda
        registro.capture_date = capture_date
        db.commit()
    return RedirectResponse(url="/cc2026", status_code=303)

@router.post("/{radicacion}/eliminar")
def eliminar(
    radicacion: str,
    db: Session = Depends(get_db),
    usuario=Depends(requerir_permiso("eliminar")),
):
    registro = db.query(CC2026).filter(CC2026.radicacion == radicacion).first()
    if registro:
        db.delete(registro)
        db.commit()
    return RedirectResponse(url="/cc2026", status_code=303)