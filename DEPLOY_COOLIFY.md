# Despliegue en Coolify — API Ruteros (FastAPI)

Guía para alinear **puerto del contenedor**, **proxy** y **healthchecks** con este repositorio.

## Resumen

| Concepto | Valor |
|----------|--------|
| Dominio API | `https://api-ruteros.edwuarcardenas.online` |
| PocketBase | Variable `POCKETBASE_URL` (URL pública **o** interna Docker; ver abajo) |
| Puerto interno del contenedor | **8000** |
| Comando de arranque | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

Coolify/Nixpacks pueden inyectar `PORT=8000`. El `Dockerfile` usa `uvicorn ... --port ${PORT}` (por defecto 8000).

## Configuración en Coolify (aplicación API)

### Build

- **Repositorio:** `winer38zE/ruteros_venezuela`
- **Rama:** `main` (o la rama del PR que despliegues)
- **Build pack:** Nixpacks o Dockerfile (ambos exponen puerto 8000)

### Start command

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Si Coolify define `PORT`, puedes usar:

```bash
sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'
```

### Ports / Networking

- **Ports exposes:** `8000`
- **Port mappings:** vacío (Coolify enruta el dominio al puerto expuesto del contenedor)
- **Dominio:** `https://api-ruteros.edwuarcardenas.online` → puerto de destino **8000** (no 8086)

### Healthchecks

| Ruta | Uso | Código esperado |
|------|-----|-----------------|
| `GET /health` | Liveness — el proceso FastAPI responde | **200** |
| `GET /health/ready` | Readiness — PocketBase init + probe OK | **200** cuando PB listo; **503** mientras arranca |

Recomendación:

- **Liveness:** `/health` (intervalo corto)
- **Readiness / tráfico:** `/health/ready` (evita Bad Gateway si el proxy enruta antes de que PocketBase esté listo)

### Variables de entorno (sin valores reales)

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `POCKETBASE_URL` | Sí | URL pública o interna de PocketBase |
| `ADMIN_EMAIL` | Sí | Email del superusuario PocketBase |
| `ADMIN_PASSWORD` | Sí | Contraseña del superusuario |
| `JWT_SECRET_KEY` | Recomendada | Firma de tokens JWT (si usas endpoints que emiten JWT) |
| `DEMO_PASSWORD` | Opcional | Clave demo; mínimo 12 caracteres o el arranque no sincroniza cuentas demo |
| `DEMO_USERS_ENABLED` | Opcional | En producción (`ENVIRONMENT=production`) el default es `false`. Pon `true` solo si aún usas dueno/vendedor/cobrador |
| `ENVIRONMENT` | Recomendada | `production` en Coolify para desactivar demo por defecto |
| `PORT` | Opcional | Debe ser **8000** si el proxy apunta a 8000 |
| `CORS_ORIGINS` | Opcional | Orígenes permitidos, separados por coma |
| `PB_COLLECTIONS_CACHE_TTL` | Opcional | Segundos de caché del listado de colecciones (default 300) |
| `POCKETBASE_INIT_RETRY_SECONDS` | Opcional | Segundos entre ciclos de init en segundo plano (default 30) |

No configures en el repo secretos reales; solo en el panel de Coolify.

## PocketBase y API en la red interna de Docker (recomendado)

Si la API y PocketBase están en el **mismo servidor Coolify**, evita salir a internet y volver por Traefik (502 intermitentes): conecta ambos contenedores a la red **`coolify`** y apunta `POCKETBASE_URL` al **nombre del contenedor** de PocketBase en el puerto interno (8090).

Ejemplo (sustituye el nombre real del contenedor PB):

```env
POCKETBASE_URL=http://ruteros-db-aislada-poi5og3l9bhcek4n5yq5p6ub:8090
```

### Pasos en Coolify

1. En el servicio **PocketBase** → **Network** / redes: adjuntar la red `coolify` (si no está ya).
2. En el servicio **API** (FastAPI) → **Network**: la misma red `coolify`.
3. En **Variables de entorno** de la API, setear `POCKETBASE_URL` con `http://<nombre-contenedor-pb>:8090` (sin barra final).
4. Redeploy de la API.

### Comprobar que comparten red (terminal del contenedor API)

```bash
# Nombre del host PocketBase (debe resolver)
getent hosts ruteros-db-aislada-poi5og3l9bhcek4n5yq5p6ub

# Health directo a PocketBase (debe ser 200)
curl -s -o /dev/null -w "%{http_code}\n" http://ruteros-db-aislada-poi5og3l9bhcek4n5yq5p6ub:8090/api/health

# Diagnóstico 30 peticiones (script del repo)
python scripts/diagnostico_pb.py
```

Si `getent` no resuelve, los contenedores **no** están en la misma red Docker.

Variables opcionales de afinado HTTP hacia PocketBase:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `PB_HTTP_KEEPALIVE_EXPIRY` | `5` | Segundos de keepalive (conexiones cortas ante proxies) |
| `PB_COLLECTIONS_CACHE_TTL` | `300` | Caché del listado de colecciones |

## Verificar que proxy y app usan el mismo puerto

Desde tu máquina (sustituye el dominio si aplica):

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://api-ruteros.edwuarcardenas.online/health
```

Debe devolver `200` cuando el contenedor esté arriba (aunque PocketBase aún no esté listo).

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://api-ruteros.edwuarcardenas.online/health/ready
```

- `503` → API viva pero PocketBase/init pendiente (normal justo tras deploy).
- `200` → listo para login y `/docs`.

Dentro del contenedor (Coolify → Terminal):

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/health
```

Si esto da `200` pero el dominio público da **502 Bad Gateway**, el proxy apunta a un puerto distinto de **8000**.

## Login demo tras deploy

Cuando `/health/ready` sea 200, prueba:

```bash
curl -s -X POST "https://api-ruteros.edwuarcardenas.online/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"dueno","password":"<DEMO_PASSWORD>"}'
```

## App móvil

URL base: `https://api-ruteros.edwuarcardenas.online/api/v1` (ver `mobile/lib/config/api_config.dart`).
