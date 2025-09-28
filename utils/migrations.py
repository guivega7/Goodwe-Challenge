"""Lightweight migration helpers for SQLite.

Currently adds new columns to existing tables when they are missing.
This avoids introducing a full migration framework (Alembic) right now.

Usage: call apply_migrations(app) after db.create_all().
"""
from typing import Iterable
from extensions import db


def _column_exists(table: str, column: str) -> bool:
    cur = db.session.execute(f"PRAGMA table_info({table})")
    for row in cur:  # row: (cid, name, type, notnull, dflt_value, pk)
        if row[1] == column:
            return True
    return False


def _add_column(table: str, column_def: str):
    # SQLite supports simple ADD COLUMN (always adds at end)
    db.session.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")


def apply_migrations():  # no app arg needed when called inside app_context
    """Run idempotent column additions."""
    # aparelhos: add codigo_externo, origem
    changes: list[str] = []
    if _column_exists('aparelhos', 'id'):  # table exists
        if not _column_exists('aparelhos', 'codigo_externo'):
            _add_column('aparelhos', 'codigo_externo VARCHAR(100)')
            changes.append('aparelhos.codigo_externo')
        if not _column_exists('aparelhos', 'origem'):
            _add_column('aparelhos', 'origem VARCHAR(30)')
            changes.append('aparelhos.origem')
    if changes:
        db.session.commit()
    else:
        # Still flush (no-op) to keep consistent session state
        db.session.flush()
    return changes
