
try:
    with open("test_debug.txt", "r", encoding="utf-16le") as f:
        print(f.read())
except Exception as e:
    print(f"Failed to read utf-16le: {e}")
    # Try utf-8 just in case
    try:
        with open("test_debug.txt", "r", encoding="utf-8") as f:
            print(f.read())
    except Exception as e2:
        print(f"Failed to read utf-8: {e2}")
