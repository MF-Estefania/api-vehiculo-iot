from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.security import requerir_administradora
from app.services.admin_service import AdminService
from app.services.auditoria_service import AuditoriaService

router = APIRouter(prefix="/admin", tags=["Administración IoT"])
admin_service = AdminService()
auditoria_service = AuditoriaService()


class ModeloCrear(BaseModel):
    nombre_modelo: str = Field(..., min_length=1, max_length=80)
    descripcion: str = Field("", max_length=255)
    microcontrolador: str = Field("ESP8266", max_length=50)
    activo: bool = True


class UnidadCrear(BaseModel):
    id_modelo: int = Field(1, gt=0)
    nombre: str = Field(..., min_length=1, max_length=80)
    modelo: str = Field("TR-01", max_length=80)
    numero_serie: str = Field(..., min_length=1, max_length=50)
    descripcion: str = Field("", max_length=255)
    microcontrolador: str = Field("ESP8266", max_length=50)
    id_propietario: int | None = None
    estado_comercial: str = Field("disponible", pattern="^(disponible|vendido|exhibicion|mantenimiento)$")
    activo: bool = True


class AsignacionRequest(BaseModel):
    id_vehiculo: int = Field(..., gt=0)
    id_usuario: int | None = None
    estado_comercial: str | None = None


@router.get("/dashboard")
def obtener_dashboard(admin: dict = Depends(requerir_administradora)):
    return admin_service.obtener_metricas()


@router.get("/modelos")
def listar_modelos(admin: dict = Depends(requerir_administradora)):
    return admin_service.listar_modelos()


@router.post("/modelos", status_code=201)
def crear_modelo(datos: ModeloCrear, request: Request, admin: dict = Depends(requerir_administradora)):
    modelo = admin_service.crear_modelo(datos.model_dump())
    auditoria_service.registrar(
        accion="CREAR_MODELO",
        recurso=f"modelo/{modelo['id_modelo']}",
        detalle=f"Modelo {modelo['nombre_modelo']} registrado",
        id_usuario=admin.get("id_usuario"),
        nombre_usuario=admin.get("nombre_usuario"),
        rol=admin.get("rol"),
        ip_origen=request.client.host if request.client else None,
    )
    return modelo


@router.put("/modelos/{id_modelo}")
def actualizar_modelo(id_modelo: int, datos: ModeloCrear, request: Request, admin: dict = Depends(requerir_administradora)):
    modelo = admin_service.actualizar_modelo(id_modelo, datos.model_dump())
    auditoria_service.registrar(
        accion="ACTUALIZAR_MODELO",
        recurso=f"modelo/{id_modelo}",
        detalle=f"Modelo {modelo['nombre_modelo']} actualizado",
        id_usuario=admin.get("id_usuario"),
        nombre_usuario=admin.get("nombre_usuario"),
        rol=admin.get("rol"),
        ip_origen=request.client.host if request.client else None,
    )
    return modelo


@router.get("/unidades")
def listar_unidades(admin: dict = Depends(requerir_administradora)):
    return admin_service.listar_unidades()


@router.post("/unidades", status_code=201)
def crear_unidad(datos: UnidadCrear, request: Request, admin: dict = Depends(requerir_administradora)):
    unidad = admin_service.crear_unidad(datos.model_dump())
    auditoria_service.registrar(
        accion="ALTA_UNIDAD",
        recurso=f"vehiculo/{unidad['id_vehiculo']}",
        detalle=f"Unidad {unidad['numero_serie']} ({unidad['nombre']}) dada de alta como {unidad['estado_comercial']}",
        id_usuario=admin.get("id_usuario"),
        nombre_usuario=admin.get("nombre_usuario"),
        rol=admin.get("rol"),
        ip_origen=request.client.host if request.client else None,
    )
    return unidad


@router.put("/unidades/{id_vehiculo}")
def actualizar_unidad(id_vehiculo: int, datos: UnidadCrear, request: Request, admin: dict = Depends(requerir_administradora)):
    unidad = admin_service.actualizar_unidad(id_vehiculo, datos.model_dump())
    auditoria_service.registrar(
        accion="MODIFICAR_UNIDAD",
        recurso=f"vehiculo/{id_vehiculo}",
        detalle=f"Unidad {id_vehiculo} modificada",
        id_usuario=admin.get("id_usuario"),
        nombre_usuario=admin.get("nombre_usuario"),
        rol=admin.get("rol"),
        ip_origen=request.client.host if request.client else None,
    )
    return unidad


@router.post("/asignaciones")
def asignar_unidad(datos: AsignacionRequest, request: Request, admin: dict = Depends(requerir_administradora)):
    unidad = admin_service.asignar_unidad(datos.id_vehiculo, datos.id_usuario, datos.estado_comercial)
    auditoria_service.registrar(
        accion="ASIGNAR_PROPIETARIO",
        recurso=f"vehiculo/{datos.id_vehiculo}",
        detalle=f"Unidad {datos.id_vehiculo} asignada a usuario ID {datos.id_usuario} con estado {unidad['estado_comercial']}",
        id_usuario=admin.get("id_usuario"),
        nombre_usuario=admin.get("nombre_usuario"),
        rol=admin.get("rol"),
        ip_origen=request.client.host if request.client else None,
    )
    return unidad


@router.get("/clientes")
def listar_clientes(admin: dict = Depends(requerir_administradora)):
    return admin_service.listar_clientes()


@router.get("/auditoria")
def consultar_auditoria(limite: int = Query(50, le=200), admin: dict = Depends(requerir_administradora)):
    return auditoria_service.listar(limite=limite)
