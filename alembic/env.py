
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Dodanie katalogu głównego projektu do ścieżki Pythona
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base
import models  # noqa

# Konfiguracja Alembica
config = context.config

# Adres bazy danych ze zmiennej środowiskowej lub domyślnie SQLite
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", "sqlite:///./lab02.db"),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadane modeli potrzebne do autogenerowania migracji
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Uruchomienie migracji w trybie offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Uruchomienie migracji w trybie online."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
