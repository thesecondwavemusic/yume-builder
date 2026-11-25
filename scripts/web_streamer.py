#!/usr/bin/env python3
import http.server
import os
import subprocess
import sys
import urllib.parse

PORT = int(os.environ.get("PORT", "8080"))

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Yume Creator Cloud · macOS Live Remote</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    header {
      background: #161b22;
      border-bottom: 1px solid #30363d;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-shrink: 0;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      font-size: 14px;
      color: #58a6ff;
    }
    .controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    button {
      background: #238636;
      color: #fff;
      border: 1px solid rgba(240,246,252,0.1);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    button:hover { background: #2ea043; }
    button.secondary { background: #21262d; color: #c9d1d9; border-color: #30363d; }
    button.secondary:hover { background: #30363d; }
    input[type="text"] {
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 6px 10px;
      color: #fff;
      font-size: 12px;
      width: 220px;
    }
    input[type="text"]:focus { outline: 1px solid #58a6ff; }
    #viewport-container {
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 8px;
      background: #010409;
      position: relative;
    }
    #screen {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6);
      border-radius: 6px;
      border: 1px solid #30363d;
      cursor: crosshair;
      user-select: none;
    }
    .status-pill {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      background: #1f6feb22;
      color: #58a6ff;
      border: 1px solid #1f6feb66;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span>🍏</span> Yume Creator Cloud · macOS Sonoma Interactive Console
      <span class="status-pill" id="status">Conectado (Live)</span>
    </div>
    <div class="controls">
      <input type="text" id="type-input" placeholder="Escribe texto y pulsa Enviar..." onkeydown="if(event.key==='Enter') sendType()">
      <button onclick="sendType()">⌨️ Escribir</button>
      <button class="secondary" onclick="sendKey('Return')">↵ Enter</button>
      <button class="secondary" onclick="sendKey('Backspace')">⌫ Borrar</button>
      <button class="secondary" onclick="sendKey('Escape')">Esc</button>
      <button class="secondary" onclick="sendKey('Space')">Espacio</button>
      <button class="secondary" onclick="forceRefresh()">🔄 Refrescar</button>
    </div>
  </header>

  <div id="viewport-container">
    <img id="screen" src="/screen.jpg" alt="macOS Screen" onclick="handleClick(event)" ondblclick="handleDoubleClick(event)" oncontextmenu="handleRightClick(event); return false;">
  </div>

  <script>
    const img = document.getElementById('screen');
    const status = document.getElementById('status');
    let isBusy = false;

    function refreshScreen() {
      if (isBusy) return;
      const nextImg = new Image();
      nextImg.src = '/screen.jpg?t=' + Date.now();
      nextImg.onload = () => {
        img.src = nextImg.src;
        status.textContent = 'En vivo · ' + new Date().toLocaleTimeString();
        status.style.color = '#58a6ff';
      };
      nextImg.onerror = () => {
        status.textContent = 'Reconectando...';
        status.style.color = '#f85149';
      };
    }

    // Auto-refresh every 1.2 seconds for fluid interactivity
    setInterval(refreshScreen, 1200);

    function getCoords(e) {
      const rect = img.getBoundingClientRect();
      const scaleX = img.naturalWidth / rect.width;
      const scaleY = img.naturalHeight / rect.height;
      return {
        x: Math.round((e.clientX - rect.left) * scaleX),
        y: Math.round((e.clientY - rect.top) * scaleY)
      };
    }

    function handleClick(e) {
      const { x, y } = getCoords(e);
      status.textContent = 'Clic en (' + x + ', ' + y + ')...';
      fetch('/click?mode=click&x=' + x + '&y=' + y)
        .then(() => setTimeout(refreshScreen, 400));
    }

    function handleDoubleClick(e) {
      const { x, y } = getCoords(e);
      status.textContent = 'Doble clic en (' + x + ', ' + y + ')...';
      fetch('/click?mode=double&x=' + x + '&y=' + y)
        .then(() => setTimeout(refreshScreen, 400));
    }

    function handleRightClick(e) {
      e.preventDefault();
      const { x, y } = getCoords(e);
      status.textContent = 'Clic derecho en (' + x + ', ' + y + ')...';
      fetch('/click?mode=right&x=' + x + '&y=' + y)
        .then(() => setTimeout(refreshScreen, 400));
      return false;
    }

    function sendType() {
      const input = document.getElementById('type-input');
      const val = input.value;
      if (!val) return;
      status.textContent = 'Escribiendo...';
      fetch('/type?text=' + encodeURIComponent(val))
        .then(() => {
          input.value = '';
          setTimeout(refreshScreen, 400);
        });
    }

    function sendKey(key) {
      status.textContent = 'Tecla ' + key + '...';
      fetch('/keypress?key=' + encodeURIComponent(key))
        .then(() => setTimeout(refreshScreen, 400));
    }

    function forceRefresh() {
      img.src = '/screen.jpg?t=' + Date.now();
    }
  </script>
</body>
</html>
"""

class LiveHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/' or parsed.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif parsed.path == '/screen.jpg':
            tmp_img = '/tmp/live_screen.jpg'
            subprocess.run(['screencapture', '-x', '-t', 'jpg', tmp_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(tmp_img):
                with open(tmp_img, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(500)
                self.end_headers()
        elif parsed.path == '/click':
            qs = urllib.parse.parse_qs(parsed.query)
            x = qs.get('x', ['0'])[0]
            y = qs.get('y', ['0'])[0]
            mode = qs.get('mode', ['click'])[0]
            cmd = 'c'
            if mode == 'double':
                cmd = 'dc'
            elif mode == 'right':
                cmd = 'rc'
            subprocess.run(['cliclick', f'{cmd}:{x},{y}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif parsed.path == '/type':
            qs = urllib.parse.parse_qs(parsed.query)
            text = qs.get('text', [''])[0]
            safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
            subprocess.run(['osascript', '-e', f'tell application "System Events" to keystroke "{safe_text}"'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif parsed.path == '/keypress':
            qs = urllib.parse.parse_qs(parsed.query)
            key = qs.get('key', ['Return'])[0]
            key_codes = {
                'Return': 36,
                'Space': 49,
                'Backspace': 51,
                'Escape': 53,
                'Tab': 48,
                'Up': 126,
                'Down': 125,
            }
            code = key_codes.get(key, 36)
            subprocess.run(['osascript', '-e', f'tell application "System Events" to key code {code}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass # Silence request logs for speed

if __name__ == '__main__':
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), LiveHandler)
    print(f"==> Live macOS Web Remote running on port {PORT}...")
    server.serve_forever()
