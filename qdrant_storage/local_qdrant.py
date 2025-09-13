
import os
import sys
from qdrant_client import QdrantClient
from qdrant_client.http import models
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    server = HTTPServer(('localhost', 6333), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    print("Starting local Qdrant simulation...")
    # Start health endpoint
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    print("Qdrant local simulation running on http://localhost:6333")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
