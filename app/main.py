from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import DatabaseError
from app.exceptions import RecursoNoEncontrado
from app.routers import vehiculos

app = FastAPI(
    title="API Vehículo IoT",
    description="API local (Dev) para el vehículo IoT, con Amazon RDS y WebSocket.",
    version="1.0.0",
)


@app.exception_handler(RecursoNoEncontrado)
async def manejar_no_encontrado(request: Request, exc: RecursoNoEncontrado):
    return JSONResponse(status_code=404, content={"detail": exc.mensaje})


@app.exception_handler(DatabaseError)
async def manejar_error_bd(request: Request, exc: DatabaseError):
    # Mensaje genérico: nunca exponemos credenciales ni detalles internos.
    return JSONResponse(status_code=503, content={"detail": "Servicio de datos no disponible"})


app.include_router(vehiculos.router)