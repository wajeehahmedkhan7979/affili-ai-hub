"""
Custom UUID type for SQLAlchemy that works correctly across SQLite and Postgres.
Handles Python 3.13 compatibility issues.
"""
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid as py_uuid


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36), storing as stringified hex values.
    
    Compatible with Python 3.13's stricter uuid.UUID constructor.
    """
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, py_uuid.UUID):
                return str(py_uuid.UUID(value))
            else:
                return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif not isinstance(value, py_uuid.UUID):
            # Ensure we're passing a string to UUID constructor
            return py_uuid.UUID(str(value))
        else:
            return value
