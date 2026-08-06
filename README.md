# Ruteros Venezuela — Backend API

API FastAPI para el sistema Ruteros (ventas, cobros, inventario, contabilidad y finanzas).

## Requisitos

- Python 3.12+ **o** Docker
- Git

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
```

La base de datos SQLite se guarda en el volumen Docker `ruteros_data`.

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
  core/         # Configuración, DB, auth
  models/       # Modelos SQLAlchemy
  schemas/      # Schemas Pydantic
  services/     # Lógica de negocio
scripts/        # Utilidades (seed, etc.)
```
