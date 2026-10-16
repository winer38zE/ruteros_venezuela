# Despliegue en Coolify — API Ruteros (FastAPI)

Guía para alinear **puerto del contenedor**, **proxy** y **healthchecks** con este repositorio.

## Resumen

| Concepto | Valor |
|----------|--------|
| Dominio API | `https://api-ruteros.edwuarcardenas.online` |
| PocketBase (externo) | `https://ruteros.edwuarcardenas.online` → variable `POCKETBASE_URL` |
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
| `DEMO_PASSWORD` | Opcional | Clave de usuarios demo; por defecto `123456` en código |
| `PORT` | Opcional | Debe ser **8000** si el proxy apunta a 8000 |
| `CORS_ORIGINS` | Opcional | Orígenes permitidos, separados por coma |
| `PB_COLLECTIONS_CACHE_TTL` | Opcional | Segundos de caché del listado de colecciones (default 300) |
| `POCKETBASE_INIT_RETRY_SECONDS` | Opcional | Segundos entre ciclos de init en segundo plano (default 30) |

No configures en el repo secretos reales; solo en el panel de Coolify.

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
