import os

# Local: sqlite:///./ruteros_local.db
# Docker/VPS: sqlite:////app/data/ruteros.db (volumen persistente)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ruteros_local.db")