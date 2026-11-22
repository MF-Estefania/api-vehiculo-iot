from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import DatabaseError
from app.exceptions import ConflictoError, RecursoNoEncontrado
from app.routers import (
    admin,
    auth,
    comandos,
    demos,
    estado,
    historial,
    invitado,
    mis_vehiculos,
    movimientos,
    sistema,
    vehiculos,
    ws,
)

app = FastAPI(
    title="API Vehículo IoT - SCARLETTE 4.3",
    description="Plataforma comercial multiusuario: ADMINISTRACIÓN + CONTROL + MONITOREO con roles Administrador, Usuario e Invitado.",
    version="4.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mf-estefania.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RecursoNoEncontrado)
async def manejar_no_encontrado(request: Request, exc: RecursoNoEncontrado):
    return JSONResponse(status_code=404, content={"detail": exc.mensaje})


@app.exception_handler(ConflictoError)
async def manejar_conflicto(request: Request, exc: ConflictoError):
    return JSONResponse(status_code=409, content={"detail": exc.mensaje})


@app.exception_handler(DatabaseError)
async def manejar_error_bd(request: Request, exc: DatabaseError):
    return JSONResponse(status_code=503, content={"detail": "Servicio de datos no disponible"})


# Routers existentes (4.1 y 4.2)
app.include_router(vehiculos.router)
app.include_router(comandos.router)
app.include_router(estado.router)
app.include_router(historial.router)
app.include_router(movimientos.router)
app.include_router(movimientos.router_stop)
app.include_router(ws.router)
app.include_router(demos.router)
app.include_router(auth.router)

# Routers nuevos (4.3 ADMINISTRACIÓN, CLIENTES, INVITADOS, DIAGNÓSTICO)
app.include_router(admin.router)
app.include_router(invitado.router)
app.include_router(mis_vehiculos.router)
app.include_router(sistema.router)
