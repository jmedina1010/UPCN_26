from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

import crud
from models import init_db, SessionLocal, User

app = FastAPI(title="UPCN - Padrón")
app.add_middleware(SessionMiddleware, secret_key="change-me-please", same_site="lax")

templates = Jinja2Templates(directory="templates")

# Carpeta static (logo.png)
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def _startup() -> None:
    init_db()


def current_user(request: Request, db: Session) -> Optional[User]:
    uid = request.session.get("uid")
    if not uid:
        return None
    return db.query(User).filter(User.id == uid).first()


@app.get("/", response_class=HTMLResponse)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/padron", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    u = crud.authenticate_user(db, email, password)
    if not u:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Credenciales incorrectas"},
            status_code=401,
        )
    request.session["uid"] = u.id
    return RedirectResponse(url="/padron", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/admin/seed_users")
async def seed_users(db: Session = Depends(get_db)):
    result = crud.seed_initial_users(db)
    return JSONResponse(result)


@app.get("/admin/upload", response_class=HTMLResponse)
async def upload_form(request: Request, db: Session = Depends(get_db)):
    u = current_user(request, db)
    if not u:
        return RedirectResponse(url="/login", status_code=302)
    if u.role != "admin":
        return HTMLResponse("Forbidden", status_code=403)

    return templates.TemplateResponse("upload.html", {"request": request, "user": u})


@app.post("/admin/upload")
async def upload_post(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    u = current_user(request, db)
    if not u:
        return RedirectResponse(url="/login", status_code=302)
    if u.role != "admin":
        return HTMLResponse("Forbidden", status_code=403)

    data = await file.read()
    text = data.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    rows = []
    for r in reader:
        dni = r.get("dni") or r.get("DNI") or r.get("documento") or r.get("Documento")
        nombre = r.get("nombre") or r.get("Nombre")
        apellido = r.get("apellido") or r.get("Apellido")
        domicilio = r.get("domicilio") or r.get("Domicilio")
        localidad = r.get("localidad") or r.get("Localidad")
        provincia = r.get("provincia") or r.get("Provincia")

        extras = dict(r)
        for k in [
            "dni", "DNI", "documento", "Documento",
            "nombre", "Nombre",
            "apellido", "Apellido",
            "domicilio", "Domicilio",
            "localidad", "Localidad",
            "provincia", "Provincia",
        ]:
            extras.pop(k, None)

        rows.append(
            {
                "dni": dni,
                "nombre": nombre,
                "apellido": apellido,
                "domicilio": domicilio,
                "localidad": localidad,
                "provincia": provincia,
                "extras": extras,
            }
        )

    result = crud.upsert_padron_from_rows(db, rows)

    # Si querés volver a la pantalla de upload con mensaje:
    # return templates.TemplateResponse("upload.html", {"request": request, "user": u, "result": result})

    return JSONResponse({"ok": True, **result})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    u = current_user(request, db)
    if not u:
        return RedirectResponse(url="/login", status_code=302)

    # Si tu crud tiene métricas, podés reemplazar esto por datos reales
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": u})


@app.get("/padron", response_class=HTMLResponse)
async def padron_page(request: Request, q: str = "", db: Session = Depends(get_db)):
    u = current_user(request, db)
    if not u:
        return RedirectResponse(url="/login", status_code=302)

    results = crud.search_padron(db, q) if q else []
    return templates.TemplateResponse(
        "padron.html",
        {"request": request, "user": u, "q": q, "results": results},
    )