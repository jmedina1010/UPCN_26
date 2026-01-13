import os

from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError

DB_URL = "sqlite:///./padron.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Afiliado(Base):
    __tablename__ = "afiliados"
    id = Column(Integer, primary_key=True, index=True)
    legajo = Column(String(30), unique=True, index=True, nullable=False)
    nombres = Column(String(100), index=True, nullable=False)
    apellidos = Column(String(120), index=True, nullable=False)
    delegacion = Column(String(100), index=True, nullable=False)
    seccion = Column(String(20), index=True, nullable=False)

Index("idx_busqueda_nombre", Afiliado.nombres, Afiliado.apellidos)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="UPCN - Padron de Afiliados (demo)")

# Carpeta para archivos estáticos (logo, etc.)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class AfiliadoIn(BaseModel):
    legajo: str = Field(..., min_length=2, max_length=30)
    nombres: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=120)
    delegacion: str = Field(..., min_length=1, max_length=100)
    seccion: str = Field(..., min_length=1, max_length=20)

def seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(Afiliado).count() == 0:
            demo = [
                Afiliado(legajo="UPCN-0001", nombres="JUAN", apellidos="PEREZ LOPEZ", delegacion="CENTRAL", seccion="101"),
                Afiliado(legajo="UPCN-0002", nombres="MARIA", apellidos="GOMEZ", delegacion="NORTE", seccion="205"),
                Afiliado(legajo="UPCN-0003", nombres="CARLOS", apellidos="HERNANDEZ", delegacion="CENTRAL", seccion="101"),
            ]
            db.add_all(demo)
            db.commit()
    finally:
        db.close()

seed_if_empty()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UPCN - Padrón de Afiliados</title>
  <style>
    :root{
      --azul:#0b2b5b;
      --celeste:#5bc0eb;
      --blanco:#ffffff;
      --gris:#f4f7fb;
      --borde:#d9e2ef;
      --texto:#102a43;
    }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; background: var(--gris); color: var(--texto); }
    .topbar{
      background: linear-gradient(90deg, var(--azul), #0e3a7a);
      color: var(--blanco);
      padding: 18px 20px;
      border-bottom: 4px solid var(--celeste);
    }
    .container{ max-width: 1100px; margin: 18px auto; padding: 0 14px; }
    .card{
      background: var(--blanco);
      border: 1px solid var(--borde);
      border-radius: 12px;
      box-shadow: 0 8px 20px rgba(16,42,67,.06);
      overflow: hidden;
    }
    .header{
      display:flex; gap:14px; align-items:center;
      padding: 16px 18px;
      background: repeating-linear-gradient(135deg, #ffffff, #ffffff 14px, #eef6ff 14px, #eef6ff 28px);
      border-bottom: 1px solid var(--borde);
    }
    .logo{
      width: 54px; height: 54px; border-radius: 10px;
      background: rgba(11,43,91,.08);
      border: 1px solid rgba(11,43,91,.15);
      display:flex; align-items:center; justify-content:center;
      overflow:hidden;
    }
    .logo img{ width: 100%; height: 100%; object-fit: contain; background: white; }
    .title h1{ font-size: 18px; margin: 0; }
    .title p{ margin: 4px 0 0; color: #486581; font-size: 13px; }
    .toolbar{
      padding: 14px 18px;
      display:flex; gap:10px; flex-wrap: wrap;
      align-items:center;
    }
    .input{
      flex: 1 1 420px;
      display:flex; gap:10px;
    }
    input[type="text"]{
      width: 100%;
      padding: 11px 12px;
      border: 1px solid var(--borde);
      border-radius: 10px;
      font-size: 14px;
      outline: none;
    }
    input[type="text"]:focus{ border-color: var(--celeste); box-shadow: 0 0 0 3px rgba(91,192,235,.25); }
    button{
      padding: 11px 14px;
      border-radius: 10px;
      border: 1px solid rgba(11,43,91,.2);
      background: var(--azul);
      color: var(--blanco);
      font-weight: 700;
      cursor: pointer;
    }
    button:hover{ filter: brightness(1.05); }
    .meta{ font-size: 13px; color:#486581; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px 12px; border-top: 1px solid var(--borde); font-size: 14px; }
    th { background: #f8fbff; color: #334e68; text-align: left; position: sticky; top: 0; }
    .tag{
      display:inline-block; padding: 2px 8px; border-radius: 999px;
      background: rgba(91,192,235,.18); color: #0b2b5b; font-weight: 700; font-size: 12px;
      border: 1px solid rgba(91,192,235,.35);
    }
    .footer{
      padding: 12px 18px; border-top: 1px solid var(--borde);
      display:flex; justify-content: space-between; gap:10px; flex-wrap: wrap;
      background: #fff;
      color:#627d98; font-size: 12px;
    }
    @media (max-width: 640px){
      th:nth-child(1), td:nth-child(1){ display:none; }
    }
  </style>
</head>
<body>
  <div class="topbar">
    <div class="container">
      <div style="display:flex; justify-content:space-between; gap:10px; align-items:center;">
        <div style="font-weight:800; letter-spacing:.3px;">UPCN</div>
        <div style="opacity:.9; font-size:13px;">Padrón de Afiliados — Elección de Representante</div>
      </div>
    </div>
  </div>

  <div class="container">
    <div class="card">
      <div class="header">
        <div class="logo" title="Logo UPCN">
          <img src="/static/logo.png" alt="UPCN" onerror="this.style.display='none'; this.parentElement.textContent='UPCN'; this.parentElement.style.fontWeight='800'; this.parentElement.style.color='#0b2b5b';">
        </div>
        <div class="title">
          <h1>Padrón de Afiliados</h1>
          <p>Buscar por <b>legajo</b>, nombre, apellido, delegación o sección.</p>
        </div>
      </div>

      <div class="toolbar">
        <div class="input">
          <input id="q" type="text" placeholder="Ej: UPCN-0002, PEREZ, CENTRAL, 101" />
          <button onclick="buscar()">Buscar</button>
        </div>
        <div class="meta">
          Resultado: <span class="tag" id="count">0</span>
        </div>
      </div>

      <div style="max-height: 520px; overflow:auto;">
        <table>
          <thead>
            <tr>
              <th style="width:72px;">ID</th>
              <th>Legajo</th>
              <th>Nombres</th>
              <th>Apellidos</th>
              <th>Delegación</th>
              <th>Sección</th>
            </tr>
          </thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>

      <div class="footer">
        <div>Consejo: escribe parte del texto (búsqueda rápida).</div>
        <div>Privacidad: usa datos reales solo con permisos y medidas de seguridad.</div>
      </div>
    </div>
  </div>

<script>
async function buscar() {
  const q = document.getElementById("q").value || "";
  const res = await fetch(`/api/buscar?q=${encodeURIComponent(q)}&limit=100`);
  const data = await res.json();

  const tbody = document.getElementById("tbody");
  tbody.innerHTML = "";

  for (const a of data.items) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${a.id}</td>
      <td><span class="tag">${a.legajo}</span></td>
      <td>${a.nombres}</td>
      <td>${a.apellidos}</td>
      <td>${a.delegacion}</td>
      <td>${a.seccion}</td>
    `;
    tbody.appendChild(tr);
  }
  document.getElementById("count").textContent = data.items.length;
}

document.getElementById("q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") buscar();
});

buscar();
</script>
</body>
</html>
"""

@app.post("/api/afiliados")
def crear_afiliado(afiliado: AfiliadoIn):
    db = SessionLocal()
    try:
        a = Afiliado(
            legajo=afiliado.legajo.strip().upper(),
            nombres=afiliado.nombres.strip().upper(),
            apellidos=afiliado.apellidos.strip().upper(),
            delegacion=afiliado.delegacion.strip().upper(),
            seccion=afiliado.seccion.strip().upper(),
        )
        db.add(a)
        db.commit()
        db.refresh(a)
        return {"ok": True, "id": a.id}
    except IntegrityError:
        db.rollback()
        return {"ok": False, "error": "El legajo ya existe"}
    finally:
        db.close()

@app.get("/api/buscar")
def buscar(
    q: str = Query("", max_length=100),
    limit: int = Query(50, ge=1, le=200)
):
    db = SessionLocal()
    try:
        qn = q.strip().upper()
        query = db.query(Afiliado)
        if qn:
            like = f"%{qn}%"
            query = query.filter(
                (Afiliado.legajo.like(like)) |
                (Afiliado.nombres.like(like)) |
                (Afiliado.apellidos.like(like)) |
                (Afiliado.delegacion.like(like)) |
                (Afiliado.seccion.like(like))
            )
        items = query.order_by(Afiliado.id.desc()).limit(limit).all()
        return {
            "items": [
                {
                    "id": a.id,
                    "legajo": a.legajo,
                    "nombres": a.nombres,
                    "apellidos": a.apellidos,
                    "delegacion": a.delegacion,
                    "seccion": a.seccion,
                }
                for a in items
            ]
        }
    finally:
        db.close()

@app.post("/api/subir-logo")
async def subir_logo(file: UploadFile = File(...)):
    # Guarda SIEMPRE como static/logo.png (así el HTML no cambia)
    if file.content_type not in {"image/png"}:
        return {"ok": False, "error": "Sube el logo en PNG (image/png)."}
    content = await file.read()
    with open("static/logo.png", "wb") as f:
        f.write(content)
    return {"ok": True, "url": "/static/logo.png"}