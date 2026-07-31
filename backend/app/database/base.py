from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Gemeinsame deklarative SQLAlchemy-Basisklasse.

    Alle ORM-Modelle müssen von genau dieser Klasse erben, damit
    Migrationen und Metadatenregistrierung konsistent bleiben.
    """
