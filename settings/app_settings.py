import os

# Observability

LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")

# PostgreSQL

DB_HOST = os.getenv("DB_HOST", "marketeer-db")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "oops")
POSTGRES_USER = os.getenv("POSTGRES_USER", "oops")
