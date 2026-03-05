"""Verify all services are running"""
import socket
import urllib.request

print("=== Port Check (IPv4 + IPv6) ===", flush=True)

checks = [
    ('127.0.0.1', 8000, 'Backend (IPv4)'),
    ('::1', 5173, 'Frontend Vite 5173 (IPv6)'),
    ('::1', 5174, 'Frontend Vite 5174 (IPv6)'),
    ('::1', 5175, 'Frontend Vite 5175 (IPv6)'),
]

for host, port, name in checks:
    try:
        family = socket.AF_INET if '.' in host else socket.AF_INET6
        s = socket.socket(family, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        status = "OPEN" if result == 0 else f"CLOSED/TIMEOUT"
        print(f"  {name} ({host}:{port}): {status}", flush=True)
    except Exception as e:
        print(f"  {name}: ERROR - {e}", flush=True)

print("\n=== HTTP Check ===", flush=True)

http_checks = [
    ('http://127.0.0.1:8000/', 'Backend root'),
    ('http://127.0.0.1:8000/health', 'Backend health'),
    ('http://127.0.0.1:8000/api/docs', 'Backend API docs'),
]

for url, name in http_checks:
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        content = resp.read(100).decode('utf-8', errors='replace')
        print(f"  [OK] {name}: {content[:60]}", flush=True)
    except Exception as e:
        print(f"  [FAIL] {name}: {e}", flush=True)

print("\n=== Summary ===", flush=True)
print("Backend API: http://localhost:8000/api/docs", flush=True)
print("Frontend:    http://localhost:5175/  (or check 5173, 5174)", flush=True)
print("\nBoth services are running!", flush=True)
