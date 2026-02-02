"""
Base configuration for SQLAlchemy models.
All models should inherit from Base.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
