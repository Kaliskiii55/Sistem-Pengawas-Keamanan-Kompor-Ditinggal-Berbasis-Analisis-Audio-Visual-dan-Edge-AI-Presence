"""shared/dashboard_server.py — Local HTTP Dashboard Server."""

import os
import json
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

# State yang dibagikan ke dashboard
CURRENT_DASHBOARD_STATE = {
    "person_detected": True,
    "stove_active": False,
    "idle_seconds": 0,
    "overall_status": "NORMAL"
}

def update_dashboard_data(new_state: dict):
    global CURRENT_DASHBOARD_STATE
    CURRENT_DASHBOARD_STATE.update(new_state)

HTML_PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>StoveWatch Dashboard</title>
  <style>
    body { font-family: sans-serif; background: #121212; color: #fff; text-align: center; padding: 30px; }
    .card { background: #1e1e1e; max-width: 500px; margin: 20px auto; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .status { font-size: 1.8rem; font-weight: bold; padding: 15px; border-radius: 8px; margin: 20px 0; }
    .SAFE { background: #1b5e20; color: #a5d6a7; }
    .WARNING { background: #e65100; color: #ffe0b2; }
    .DANGER { background: #b71c1c; color: #ffcdd2; animation: blink 1s infinite; }
    @keyframes blink { 50% { opacity: 0.5; } }
    .metric { display: flex; justify-content: space-between; margin: 12px 0; font-size: 1.1rem; border-bottom: 1px solid #333; padding-bottom: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>StoveWatch Monitor</h2>
    <div id="statusBox" class="status SAFE">MEMUAT STATUS...</div>
    <div class="metric"><span>Keberadaan Orang:</span><strong id="person">...</strong></div>
    <div class="metric"><span>Kompor Aktif:</span><strong id="stove">...</strong></div>
    <div class="metric"><span>Waktu Ditinggal:</span><strong id="idle">0 detik</strong></div>
  </div>
  <script>
    async function refresh() {
      try {
        const res = await fetch('/api/state');
        const data = await res.json();
        const box = document.getElementById('statusBox');
        box.innerText = data.overall_status;
        box.className = 'status ' + (data.overall_status.includes('ALERT') ? 'DANGER' : data.overall_status.includes('WARNING') ? 'WARNING' : 'SAFE');
        document.getElementById('person').innerText = data.person_detected ? 'Terdeteksi' : 'Tidak Ada Orang';
        document.getElementById('stove').innerText = data.stove_active ? 'Menyala / Aktif' : 'Mati';
        document.getElementById('idle').innerText = data.idle_seconds + ' detik';
      } catch (e) {}
    }
    setInterval(refresh, 1000);
    refresh();
  </script>
</body>
</html>
"""

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(CURRENT_DASHBOARD_STATE).encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Meredam logging terminal agar terminal tetap rapi
        pass

def start_dashboard_server():
    port = int(os.getenv("DASHBOARD_PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://localhost:{port}"
    return server, thread, url