#!/usr/bin/env python
"""Raw socket HTTP request to test server"""
import socket
import time

time.sleep(1)  # Wait for server

print("Creating socket...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print("Connecting to 127.0.0.1:9002...")
    sock.connect(("127.0.0.1", 9002))
    print("Connected!")
    
    # Send HTTP request
    request = b"GET /test HTTP/1.1\r\nHost: 127.0.0.1:9002\r\nConnection: close\r\n\r\n"
    print(f"Sending request: {request}")
    sock.sendall(request)
    
    # Receive response
    print("Waiting for response...")
    response = b""
    while True:
        try:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            print(f"Received: {chunk}")
        except socket.timeout:
            break
    
    print(f"\nFull response:\n{response.decode('utf-8', errors='ignore')}")
    
finally:
    sock.close()
    print("Socket closed")
