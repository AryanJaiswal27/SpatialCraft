import os
import re
import sys
import time
import json
import shutil
import socket
import threading
import subprocess
from pathlib import Path

# Force unbuffered output
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT_DIR / "pipeline.log"

class TeeLogger:
    def __init__(self, filename, stream):
        self.filename = filename
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(data)
        except Exception:
            pass

    def flush(self):
        self.stream.flush()

sys.stdout = TeeLogger(LOG_FILE, sys.stdout)
sys.stderr = TeeLogger(LOG_FILE, sys.stderr)

BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
UPLOADS_DIR = ROOT_DIR / "uploads"
STORAGE_UPLOADS = BACKEND_DIR / "storage" / "uploads"
CLOUDFLARED_BIN = ROOT_DIR / "scripts" / "cloudflared.exe"
PYTHON_BIN = ROOT_DIR / "venv" / "Scripts" / "python.exe"
TUNNEL_URL_FILE = ROOT_DIR / "LATEST_TUNNEL_URL.txt"
FRONTEND_TUNNEL_FILE = FRONTEND_DIR / "public" / "tunnel_url.json"
DIST_TUNNEL_FILE = FRONTEND_DIR / "dist" / "tunnel_url.json"
QR_FILE = ROOT_DIR / "mobile_qr.png"
PUBLIC_QR_FILE = FRONTEND_DIR / "public" / "qr.png"
DIST_QR_FILE = FRONTEND_DIR / "dist" / "qr.png"
PROCESSED_TRACKER = ROOT_DIR / ".processed_uploads.json"

# Ensure directories
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_UPLOADS.mkdir(parents=True, exist_ok=True)

class SpatialCraftPipeline:
    def __init__(self):
        self.backend_proc = None
        self.tunnel_proc = None
        self.current_tunnel_url = None
        self.running = True
        self.processed_files = self._load_processed()

    def _load_processed(self) -> set:
        if PROCESSED_TRACKER.exists():
            try:
                with open(PROCESSED_TRACKER, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                pass
        return set()

    def _save_processed(self):
        try:
            with open(PROCESSED_TRACKER, "w", encoding="utf-8") as f:
                json.dump(list(self.processed_files), f)
        except Exception:
            pass

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def kill_lingering_processes(self):
        print("[PIPELINE] Cleaning up lingering background processes...", flush=True)
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for port in [8000, 5173]:
                try:
                    res = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
                    for line in res.strip().splitlines():
                        parts = line.split()
                        if len(parts) >= 5 and "LISTENING" in line:
                            pid = parts[-1]
                            subprocess.run(["taskkill", "/F", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

    def update_qr_and_urls(self, url: str):
        self.current_tunnel_url = url
        try:
            with open(TUNNEL_URL_FILE, "w", encoding="utf-8") as f:
                f.write(url)

            for target_path in [FRONTEND_TUNNEL_FILE, DIST_TUNNEL_FILE]:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump({"tunnel_url": url}, f)

            import qrcode
            qr = qrcode.make(url)
            qr.save(QR_FILE)
            qr.save(PUBLIC_QR_FILE)
            if DIST_QR_FILE.parent.exists():
                qr.save(DIST_QR_FILE)
            print(f"[PIPELINE // TUNNEL] URL Synchronized: {url}", flush=True)
            print(f"[PIPELINE // QR] Updated mobile_qr.png and static endpoints", flush=True)
        except Exception as e:
            print(f"[PIPELINE // ERROR] Updating QR / URL: {e}", flush=True)

    def start_backend(self):
        print("[PIPELINE] Starting Unified Production Server on Port 8000...", flush=True)
        cmd = [str(PYTHON_BIN), "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
        self.backend_proc = subprocess.Popen(cmd, cwd=str(ROOT_DIR))

    def supervise_backend(self):
        time.sleep(5)
        while self.running:
            if self.backend_proc is None or self.backend_proc.poll() is not None:
                print("[PIPELINE // BACKEND] Server process died or exited. Auto-restarting on port 8000...", flush=True)
                cmd = [str(PYTHON_BIN), "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
                self.backend_proc = subprocess.Popen(cmd, cwd=str(ROOT_DIR))
            time.sleep(3)

    def supervise_tunnel(self):
        time.sleep(2)
        while self.running:
            if not CLOUDFLARED_BIN.exists():
                print("[PIPELINE // TUNNEL] cloudflared.exe not found in scripts/. Downloading latest binary...", flush=True)
                try:
                    CLOUDFLARED_BIN.parent.mkdir(parents=True, exist_ok=True)
                    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
                    urllib.request.urlretrieve(url, str(CLOUDFLARED_BIN))
                    print("[PIPELINE // TUNNEL] cloudflared.exe downloaded successfully!", flush=True)
                except Exception as e:
                    print(f"[PIPELINE // TUNNEL ERROR] Failed downloading cloudflared.exe: {e}", flush=True)
                    time.sleep(10)
                    continue

            print("[PIPELINE // TUNNEL] Establishing Cloudflare Ingress Tunnel (Protocol: HTTP/2)...", flush=True)
            # Directly tunnel port 8000 for instant single-packet delivery
            cmd = [str(CLOUDFLARED_BIN), "tunnel", "--protocol", "http2", "--url", "http://localhost:8000"]
            self.tunnel_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace"
            )

            for line in self.tunnel_proc.stdout:
                if not self.running:
                    break
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    new_url = match.group(0)
                    if new_url != self.current_tunnel_url:
                        self.update_qr_and_urls(new_url)
                        print("-" * 65, flush=True)
                        print(f"[LIVE PUBLIC MOBILE ENDPOINT] : {new_url}", flush=True)
                        print(f"[LOCAL AREA ENDPOINT]         : http://{self.get_local_ip()}:8000", flush=True)
                        print("-" * 65, flush=True)

            if self.running:
                print("[PIPELINE // TUNNEL] Tunnel connection dropped. Auto-reconnecting in 3s...", flush=True)
                time.sleep(3)

    def tunnel_health_watchdog(self):
        import urllib.request
        consecutive_failures = 0
        while self.running:
            time.sleep(25)
            if not self.current_tunnel_url:
                continue

            # Check if local backend is responding first
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/api/scenes", timeout=4) as resp:
                    pass
            except Exception:
                continue

            try:
                req = urllib.request.Request(self.current_tunnel_url, headers={"User-Agent": "Watchdog/1.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                if consecutive_failures >= 4:
                    print(f"[PIPELINE // WATCHDOG] Tunnel probe attempt failed ({consecutive_failures}/4): {e}", flush=True)
                    print("[PIPELINE // WATCHDOG] Recycling tunnel...", flush=True)
                    consecutive_failures = 0
                    if self.tunnel_proc:
                        try:
                            self.tunnel_proc.terminate()
                        except Exception:
                            pass

    def folder_watcher_loop(self):
        print("[PIPELINE // WATCHER] Active. Monitoring 'uploads/' for incoming images...", flush=True)
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

        while self.running:
            try:
                self.processed_files = self._load_processed()
                for file_path in UPLOADS_DIR.iterdir():
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() not in valid_exts:
                        continue
                    if file_path.name in self.processed_files:
                        continue

                    initial_size = file_path.stat().st_size
                    time.sleep(0.5)
                    if file_path.stat().st_size != initial_size or initial_size == 0:
                        continue

                    print(f"\n[PIPELINE // WATCHER] Detected new room photo: {file_path.name}", flush=True)
                    self.processed_files.add(file_path.name)
                    self._save_processed()

                    dest_path = STORAGE_UPLOADS / file_path.name
                    if file_path.resolve() != dest_path.resolve():
                        shutil.copy2(file_path, dest_path)

                    self.trigger_automation(dest_path)

            except Exception as e:
                print(f"[PIPELINE // WATCHER ERROR] {e}", flush=True)

            time.sleep(2)

    def trigger_automation(self, image_path: Path):
        print(f"[PIPELINE // RUNNER] Ingesting {image_path.name} into automation pipeline...", flush=True)
        script = f"""
import asyncio
import json
import urllib.request
from pathlib import Path
from backend.config import get_current_engine
from backend.services.browser_automation import automate_llm_in_browser

target = get_current_engine()
img = Path(r'{str(image_path)}')
stem = img.stem
if stem.startswith('scene_'):
    parts = stem.split('_')
    scene_id = f'scene_{{parts[1]}}'
else:
    scene_id = f'scene_{{stem[:8]}}'

print(f'Ingesting scene {{scene_id}} with engine: {{target}}', flush=True)
if target == 'physical':
    try:
        data = json.dumps({{
            'job_type': 'initial_reconstruction',
            'scene_id': scene_id,
            'image_path': str(img.resolve())
        }}).encode('utf-8')
        req = urllib.request.Request('http://localhost:8000/api/physical_clicks/queue', data=data, headers={{'Content-Type': 'application/json'}})
        urllib.request.urlopen(req, timeout=5)
        print(f'Enqueued physical click job for {{scene_id}}!', flush=True)
    except Exception as e:
        print(f'Physical queue error: {{e}}', flush=True)
else:
    asyncio.run(automate_llm_in_browser(target=target, image_path=img, scene_id=scene_id))
"""
        cmd = [str(PYTHON_BIN), "-u", "-c", script]
        subprocess.Popen(cmd, cwd=str(ROOT_DIR))

    def run(self):
        print("=" * 65, flush=True)
        print("    SPATIALCRAFT // UNIFIED PRODUCTION PIPELINE", flush=True)
        print("=" * 65, flush=True)

        self.kill_lingering_processes()

        # 1. Start unified server
        self.start_backend()

        backend_supervisor_thread = threading.Thread(target=self.supervise_backend, daemon=True)
        backend_supervisor_thread.start()

        # 2. Start tunnel & watchdog
        tunnel_thread = threading.Thread(target=self.supervise_tunnel, daemon=True)
        tunnel_thread.start()

        watchdog_thread = threading.Thread(target=self.tunnel_health_watchdog, daemon=True)
        watchdog_thread.start()

        # 3. Start folder watcher
        watcher_thread = threading.Thread(target=self.folder_watcher_loop, daemon=True)
        watcher_thread.start()

        print("[PIPELINE] All services operational. Press Ctrl+C to terminate.", flush=True)
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[PIPELINE] Terminating services...", flush=True)
            self.running = False
            if self.backend_proc:
                self.backend_proc.terminate()
            if self.tunnel_proc:
                self.tunnel_proc.terminate()
            print("[PIPELINE] Shutdown complete.", flush=True)

if __name__ == "__main__":
    pipeline = SpatialCraftPipeline()
    pipeline.run()
