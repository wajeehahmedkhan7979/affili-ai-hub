
import re

def scan():
    try:
        content = ""
        try:
            with open("test_debug.txt", "r", encoding="utf-16le") as f:
                content = f.read()
        except:
            with open("test_debug.txt", "r", encoding="utf-8") as f:
                content = f.read()

        lines = content.splitlines()
        for i in range(10, min(len(lines), 50)):
            print(f"Line {i}: {lines[i]}")
    except Exception as e:
        print(f"Scan failed: {e}")

if __name__ == "__main__":
    scan()
