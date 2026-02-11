import uuid
import sys

def debug_uuid():
    print(f"Python Version: {sys.version}")
    
    # Test 1: Standard string
    val_str = "66f36618-29a3-4a1e-8e8e-67016258410e"
    print(f"Testing string: {val_str}")
    u1 = uuid.UUID(val_str)
    print(f"Success: {u1}")
    
    # Test 2: Hex string
    val_hex = "66f3661829a34a1e8e8e67016258410e"
    print(f"Testing hex: {val_hex}")
    u2 = uuid.UUID(val_hex)
    print(f"Success: {u2}")
    
    # Test 3: The Crash (int)
    val_int = 12345
    print(f"Testing int: {val_int}")
    try:
        u3 = uuid.UUID(val_int)
        print(f"Success: {u3}")
    except Exception as e:
        print(f"Caught expected crash: {e}")

    # Test 4: SQLAlchemy-style processing
    # If SQLAlchemy gets an int from a SQLite column (maybe a boolean or status code),
    # and tries to pass it to uuid.UUID() because the type is sa.UUID.
    
if __name__ == "__main__":
    debug_uuid()
