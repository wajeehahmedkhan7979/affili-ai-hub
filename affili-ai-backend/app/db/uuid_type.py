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
        if isinstance(value, py_uuid.UUID):
            return value
        
        try:
            # Handle cases where value might be bytes, int, or string
            if isinstance(value, bytes):
                return py_uuid.UUID(bytes=value)
            elif isinstance(value, int):
                # Python 3.13: Use int= explicitly
                return py_uuid.UUID(int=value)
            
            # Default to string conversion
            # For Python 3.13, ensure we are not passing an int to the first arg of UUID()
            val_str = str(value)
            
            # If it's all digits, it might be an 'int' passed as a string
            if val_str.isdigit() and len(val_str) < 32:
                 return py_uuid.UUID(int=int(val_str))
                 
            return py_uuid.UUID(val_str)
        except (AttributeError, ValueError, TypeError):
            # Fallback for weird edge cases in SQLite/3.13
            try:
                val_str = str(value)
                # If it looks like a hex string without hyphens, try that
                return py_uuid.UUID(hex=val_str)
            except Exception:
                return value
