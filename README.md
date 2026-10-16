# Ruteros Venezuela — Backend API

API FastAPI para el sistema Ruteros (ventas, cobros, inventario, contabilidad y finanzas).

## Requisitos

- Python 3.12+ **o** Docker
- Git

## Despliegue en Coolify

Ver **[DEPLOY_COOLIFY.md](./DEPLOY_COOLIFY.md)** (puerto **8000**, healthchecks, variables de entorno y alineación del proxy).

## Despliegue en VPS con Docker (recomendado)

### 1. Subir el proyecto a GitHub

Incluye en el repositorio al menos:

- `Dockerfile`
- `requirements.txt`
- `docker-compose.yml`
- carpeta `app/`

### 2. En tu VPS

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/ruteros_venezuela.git
cd ruteros_venezuela

# Levantar la API
docker compose up -d --build
```

La API quedará disponible en `http://TU_IP:8000`.

Prueba rápida:

```bash
curl http://localhost:8000/api/v1/test-conexion
```

### 3. Variables de entorno (producción)

Crea un archivo `.env` junto a `docker-compose.yml`:

```env
SECRET_KEY=una-clave-larga-y-segura
ADMIN_EMAIL=admin@tu-dominio.com
ADMIN_PASSWORD=clave-del-superusuario-pocketbase
POCKETBASE_URL=http://pocketbase:8090
```

Los datos persisten en el volumen Docker `pocketbase_data`. La API crea las colecciones al arrancar y se autentica como admin para lectura/escritura.

### Migrar datos desde SQLite antiguo

Si tienes un `ruteros_local.db` (o el volumen Docker anterior), impórtalo a PocketBase:

```bash
# PocketBase debe estar corriendo y ADMIN_EMAIL / ADMIN_PASSWORD configurados
set POCKETBASE_URL=http://127.0.0.1:8090
set ADMIN_EMAIL=admin@ruteros.local
set ADMIN_PASSWORD=tu-clave

python scripts/migrate_sqlite_to_pocketbase.py --sqlite ruteros_local.db
```

Opciones útiles:

- `--dry-run` — muestra cuántos registros migraría sin escribir.
- `--skip-existing` — solo crea IDs nuevos; no sobrescribe lo ya importado.

## Desarrollo local (sin Docker)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentación interactiva: `http://localhost:8000/docs`

## Estructura principal

```
app/
  api/          # Endpoints REST
  core/         # Configuración, PocketBase, ORM
  models/       # Modelos de dominio (mapeados a colecciones PB)
  schemas/      # Schemas Pydantic
  services/     # Lógica de negocio
scripts/        # Utilidades (seed, etc.)
```
