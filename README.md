# API Vehículo IoT (entorno Dev)

Práctica 2.5 · APIs para IoT en entorno Dev  
Autor: `Estefania Marin`

API local en Python (FastAPI) con programación orientada a objetos que controla y monitorea un vehículo IoT. Usa los 21 Stored Procedures del esquema `vehiculo_iot` alojado en Amazon RDS (MySQL) y transmite eventos en tiempo real por WebSocket.

> Alcance: esta API se ejecuta **solo en `localhost:8000`**. La publicación en un servidor público (HTTPS/WSS) corresponde a la práctica 2.6.

## Requisitos

- Python 3.11 o superior
- Visual Studio Code
- Acceso a la instancia de Amazon RDS con la base `vehiculo_iot` (regla MySQL TCP 3306 restringida a tu IP)

## Ejecución local

```powershell
git clone https://github.com/MF-Estefania/api-vehiculo-iot.git
cd api-vehiculo-iot.git

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

copy .env.example .env
# Edita .env con tus datos reales (nunca lo subas a GitHub)

uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Documentación Swagger UI: http://localhost:8000/docs

## Configuración

Las credenciales se leen de variables de entorno (archivo `.env`, excluido por `.gitignore`). El archivo `.env.example` muestra el formato **sin secretos**:

```
DB_HOST=tu-endpoint.rds.amazonaws.com
DB_PORT=3306
DB_NAME=vehiculo_iot
DB_USER=usuario
DB_PASSWORD=cambia_esto
API_KEY=cambia_esto
```

`API_KEY` protege las operaciones de eliminación y control de DEMO (ver [Seguridad](#seguridad)).

## Arquitectura (POO)

```
app/
  main.py            # crea la app, registra routers y manejadores de errores
  config.py          # clase Settings: lee y valida variables de entorno
  database.py        # clase Database: conexión a RDS, transacciones y llamada a SP
  exceptions.py      # excepciones de negocio (404 / 409)
  security.py        # autenticación por clave de API
  models/            # modelos Pydantic de entrada y salida
  services/          # reglas de negocio (una clase por área)
  routers/           # endpoints HTTP y WebSocket (sin lógica de persistencia)
  websocket/         # ConnectionManager y construcción de eventos
```

Responsabilidades:

| Capa | Responsabilidad |
|---|---|
| `routers` | Recibir la solicitud, validar con modelos, delegar al servicio |
| `services` | Reglas de negocio y coordinación de varios SP |
| `Database` | Único punto que habla con MySQL; consultas parametrizadas y transacciones |
| `ConnectionManager` | Clientes WebSocket agrupados por vehículo |
| `DemoRunner` | Ejecución de DEMO en segundo plano, concurrencia y cancelación |

## Reglas de negocio

- **Movimiento individual:** valida que el vehículo exista y esté activo, y que el comando exista, esté activo y **pertenezca a ese vehículo**. Ejecuta `sp_actualizar_estado` y `sp_registrar_historial` en **una sola transacción**; después de confirmar en RDS, notifica por WebSocket. Si se rechaza, no cambia nada y no se emite evento.
- **Campo `conectado`:** recibir una solicitud HTTP no prueba que el vehículo esté conectado, así que se conserva el valor que ya tenía (0 si no había estado).
- **Historial:** `GET .../historial` devuelve como **máximo los 10 movimientos individuales más recientes**, del más reciente al más antiguo. RDS conserva el historial completo.
- **DEMO:** los N movimientos se obtienen de `sp_obtener_movimientos_demo` y se transmiten por WebSocket respetando `duracion_ms` y `pausa_ms`. Actualiza el estado y **nunca** llama a `sp_registrar_historial`: los movimientos de DEMO no aparecen en el historial.
- **Concurrencia:** solo una DEMO por vehículo a la vez (si no, 409). Mientras corre una DEMO, también se rechazan movimientos individuales de ese vehículo.
- **Cancelación:** detiene de inmediato la DEMO activa; no se emite ningún movimiento posterior.
- Un evento `demo_movimiento` significa que la API envió esa instrucción, **no** que el vehículo físico la ejecutó; esa confirmación llegará con la integración del ESP8266/ESP32.

## Endpoints HTTP

Todas las operaciones están documentadas en Swagger UI (`/docs`) por etiquetas: Vehículos, Comandos, Estado, Historial, Movimientos y DEMO. Las escrituras usan POST; las consultas, GET.

**(P)** = protegido con `X-API-Key`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/vehiculos` | Listar vehículos |
| GET | `/vehiculos/{id}` | Obtener un vehículo |
| POST | `/vehiculos` | Crear vehículo |
| POST | `/vehiculos/{id}/actualizar` | Actualizar vehículo |
| POST | `/vehiculos/{id}/eliminar` **(P)** | Eliminar vehículo |
| GET | `/vehiculos/{id}/comandos` | Listar comandos del vehículo |
| POST | `/vehiculos/{id}/comandos` | Crear comando en el catálogo |
| POST | `/vehiculos/{id}/comandos/{id_comando}/actualizar` | Actualizar comando |
| POST | `/vehiculos/{id}/comandos/{id_comando}/eliminar` **(P)** | Eliminar comando |
| GET | `/vehiculos/{id}/estado` | Último estado (`null` si aún no tiene) |
| GET | `/vehiculos/{id}/historial` | Últimos 10 movimientos individuales |
| POST | `/vehiculos/{id}/movimientos` | Registrar un movimiento individual |
| GET | `/vehiculos/{id}/demos` | Listar DEMO del vehículo |
| POST | `/vehiculos/{id}/demos` | Crear DEMO |
| POST | `/vehiculos/{id}/demos/{id_demo}/actualizar` | Actualizar DEMO |
| POST | `/vehiculos/{id}/demos/{id_demo}/eliminar` **(P)** | Eliminar DEMO |
| GET | `/vehiculos/{id}/demos/{id_demo}/movimientos` | Movimientos ordenados de la DEMO |
| POST | `/vehiculos/{id}/demos/{id_demo}/movimientos` | Agregar movimiento a la DEMO |
| POST | `/vehiculos/{id}/demos/{id_demo}/movimientos/{id_mov}/actualizar` | Actualizar movimiento de DEMO |
| POST | `/vehiculos/{id}/demos/{id_demo}/movimientos/{id_mov}/eliminar` **(P)** | Eliminar movimiento de DEMO |
| POST | `/vehiculos/{id}/demos/{id_demo}/iniciar` **(P)** | Iniciar la DEMO (responde 202) |
| POST | `/vehiculos/{id}/demos/cancelar` **(P)** | Cancelar la DEMO en ejecución |

### Ejemplo: movimiento individual

```http
POST /vehiculos/2/movimientos
Content-Type: application/json

{ "id_comando": 17, "origen": "swagger" }
```

### Códigos HTTP usados

| Código | Cuándo |
|---|---|
| 200 / 201 / 202 | Éxito / creado / DEMO aceptada (se ejecuta en segundo plano) |
| 401 / 403 | Falta la clave de API / clave inválida |
| 404 | Recurso inexistente (o comando/DEMO de otro vehículo) |
| 409 | Conflicto: duplicado, inactivo, DEMO en ejecución, datos relacionados |
| 422 | Datos de entrada inválidos |
| 503 | Base de datos no disponible |

## WebSocket

Swagger UI no describe WebSocket de forma nativa, por eso se documenta aquí.

**URL (un canal por vehículo):**

```
ws://localhost:8000/ws/vehiculos/{id_vehiculo}
```

Cada cliente recibe únicamente los eventos del vehículo que monitorea. Se admiten varios clientes simultáneos por vehículo, y las desconexiones no afectan a los demás.

Al conectarse, el servidor consulta RDS y envía de inmediato el último estado. Si el vehículo no existe, envía un evento `error` y cierra con código `4404`; si RDS falla, cierra con `1011`.

### Formato común de los mensajes

```json
{
  "tipo": "movimiento_individual",
  "id_vehiculo": 2,
  "comando": "Avanzar",
  "codigo": 1,
  "marca_temporal": "2026-10-16T05:30:00.000000+00:00"
}
```

### Eventos

| `tipo` | Cuándo | Campos adicionales |
|---|---|---|
| `estado_inicial` | Al abrir la conexión | `estado` (objeto con el último estado, o `null`) |
| `movimiento_individual` | Tras confirmar un POST de movimiento | `origen` |
| `demo_inicio` | Comienza una DEMO | `id_demo`, `nombre_demo`, `total_movimientos` |
| `demo_movimiento` | Cada movimiento de la DEMO, en orden | `id_demo`, `nombre_demo`, `indice`, `total_movimientos`, `orden`, `duracion_ms`, `pausa_ms` |
| `demo_fin` | La DEMO terminó normalmente | `id_demo`, `nombre_demo` |
| `demo_cancelada` | La DEMO fue cancelada | `id_demo`, `nombre_demo` |
| `demo_error` | La DEMO terminó por una falla | `id_demo`, `nombre_demo`, `mensaje` |
| `error` | Error al conectar | `mensaje` |

### Ejemplo de DEMO

```json
{ "tipo": "demo_inicio", "id_vehiculo": 2, "comando": null, "codigo": null, "marca_temporal": "...", "id_demo": 1, "nombre_demo": "Demo Inicial", "total_movimientos": 2 }
{ "tipo": "demo_movimiento", "id_vehiculo": 2, "comando": "Avanzar", "codigo": 1, "marca_temporal": "...", "id_demo": 1, "indice": 1, "total_movimientos": 2, "orden": 1, "duracion_ms": 1000, "pausa_ms": 500 }
{ "tipo": "demo_fin", "id_vehiculo": 2, "comando": null, "codigo": null, "marca_temporal": "...", "id_demo": 1, "nombre_demo": "Demo Inicial" }
```

## Stored Procedures integrados (21)

| Grupo | Procedimientos |
|---|---|
| Vehículos | `sp_crear_vehiculo`, `sp_obtener_vehiculos`, `sp_obtener_vehiculo`, `sp_actualizar_vehiculo`, `sp_eliminar_vehiculo` |
| Comandos | `sp_crear_comando`, `sp_obtener_comandos_vehiculo`, `sp_actualizar_comando`, `sp_eliminar_comando` |
| Estado | `sp_actualizar_estado`, `sp_obtener_estado` |
| Historial | `sp_registrar_historial`, `sp_obtener_historial` |
| DEMO | `sp_crear_demo`, `sp_obtener_demos`, `sp_actualizar_demo`, `sp_eliminar_demo` |
| Movimientos DEMO | `sp_agregar_movimiento_demo`, `sp_obtener_movimientos_demo`, `sp_actualizar_movimiento_demo`, `sp_eliminar_movimiento_demo` |

`sp_actualizar_estado` y `sp_registrar_historial` se ejecutan dentro del endpoint de movimiento individual; `sp_actualizar_estado` también interviene durante la DEMO.

## Seguridad

- Credenciales solo en variables de entorno; `.env` está en `.gitignore`.
- Consultas parametrizadas: nunca se concatenan valores en el SQL.
- Las operaciones de eliminación y de control de DEMO (iniciar/cancelar) requieren el encabezado `X-API-Key`. Sin clave responde 401; con clave incorrecta, 403.
- Los errores devueltos al cliente no exponen credenciales ni detalles internos.
- Acceso a RDS restringido por Security Group a la IP del desarrollador, preferentemente con un usuario de MySQL de privilegios mínimos.

## Pruebas funcionales

1. **POST**: registrar un movimiento individual y verificar estado e historial.
2. **GET**: consultar el historial (máximo 10, del más reciente al más antiguo).
3. **WebSocket**: conectar al vehículo, iniciar una DEMO y verificar inicio, N movimientos en orden y fin, sin nuevos registros en el historial.