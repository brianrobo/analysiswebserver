"""
Full API integration test - Phase 4 verification
Tests: register, login, settings, analysis upload, status, result, download, history
"""
import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import time

BASE = "http://127.0.0.1:8000/api/v1"
token = None

def req(method, path, data=None, extra_headers=None):
    url = BASE + path
    h = {}
    if data is not None:
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra_headers:
        h.update(extra_headers)
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        raw = resp.read()
        try:
            return resp.status, json.loads(raw)
        except:
            return resp.status, {"_raw": raw.decode(errors="replace")[:100]}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except:
            return e.code, {"_raw": raw.decode(errors="replace")[:200]}

def check(label, code, body, expected=200):
    ok = code == expected
    icon = "[OK]" if ok else "[FAIL]"
    detail = ""
    if not ok:
        if isinstance(body, dict):
            detail = f"- {body.get('detail', body)}"
        else:
            detail = f"- {str(body)[:100]}"
    print(f"  {icon} {label} (HTTP {code}) {detail}", flush=True)
    return ok

print("=" * 55, flush=True)
print("  API Integration Test", flush=True)
print("=" * 55, flush=True)

# ---- 1. AUTH ----
print("\n[1] Auth", flush=True)
code, body = req("POST", "/auth/register", {
    "email": "testuser@example.com",
    "password": "password123",
    "full_name": "Test User"
})
if code == 200:
    check("Register (new user)", code, body)
elif "already" in str(body).lower() or code == 400:
    print("  [OK] Register - user already exists", flush=True)
else:
    check("Register", code, body)

code, body = req("POST", "/auth/login/json", {
    "email": "testuser@example.com",
    "password": "password123"
})
if check("Login", code, body):
    token = body.get("access_token")
    print(f"       Token: {token[:30]}...", flush=True)

if not token:
    print("\nCannot continue without auth token. Exiting.", flush=True)
    sys.exit(1)

code, body = req("GET", "/auth/me")
if check("Get current user (/auth/me)", code, body):
    print(f"       email={body.get('email')}, role={body.get('role')}", flush=True)

# ---- 2. SETTINGS ----
print("\n[2] Settings", flush=True)
code, body = req("GET", "/settings")
check("GET /settings", code, body)

# PATCH theme uses query param
theme_req = urllib.request.Request(
    BASE + "/settings/theme?theme=dark",
    headers={"Authorization": f"Bearer {token}"},
    method="PATCH"
)
try:
    resp = urllib.request.urlopen(theme_req, timeout=5)
    check("PATCH /settings/theme?theme=dark", resp.status, json.loads(resp.read()))
except urllib.error.HTTPError as e:
    check("PATCH /settings/theme?theme=dark", e.code, json.loads(e.read()))

# ---- 3. ANALYSIS UPLOAD ----
print("\n[3] Analysis - File Upload", flush=True)
py_code = b"""import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

def calculate_sum(a, b):
    \"\"\"Pure function - web convertible\"\"\"
    return a + b

def process_data(items):
    \"\"\"Pure function - web convertible\"\"\"
    return [x * 2 for x in items if x > 0]

def format_result(value):
    \"\"\"Pure function\"\"\"
    return f"Result: {value:.2f}"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt App")
        btn = QPushButton("Click", self)
        btn.clicked.connect(self.on_click)

    def on_click(self):
        result = calculate_sum(1, 2)
        print(format_result(result))
"""

boundary = "----FormBoundary7MA4YWxkTrZu0gW"
body_parts = [
    f"--{boundary}",
    'Content-Disposition: form-data; name="file"; filename="app.py"',
    "Content-Type: text/x-python",
    "",
    py_code.decode("utf-8"),
    f"--{boundary}--",
]
multipart_body = "\r\n".join(body_parts).encode("utf-8")

upload_req = urllib.request.Request(
    BASE + "/analysis/upload",
    data=multipart_body,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
    method="POST"
)
job_id = None
try:
    resp = urllib.request.urlopen(upload_req, timeout=30)
    upload_body = json.loads(resp.read())
    if check("POST /analysis/upload", resp.status, upload_body):
        job_id = upload_body.get("id") or upload_body.get("job_id")
        print(f"       job_id={job_id}, status={upload_body.get('status')}", flush=True)
except urllib.error.HTTPError as e:
    err_raw = e.read()
    try:
        err_body = json.loads(err_raw)
    except:
        err_body = {"_raw": err_raw.decode(errors="replace")[:300]}
    check("POST /analysis/upload", e.code, err_body)

# ---- 4. STATUS POLLING ----
if job_id:
    print(f"\n[4] Analysis Status (job_id={job_id})", flush=True)
    final_status = None
    for i in range(15):
        time.sleep(1)
        code, body = req("GET", f"/analysis/{job_id}/status")
        if isinstance(body, dict):
            st = body.get("status", "?")
            prog = body.get("progress", 0)
            print(f"       [{i+1}s] status={st}, progress={prog}%", flush=True)
            if st in ("completed", "failed"):
                final_status = st
                break
        else:
            print(f"       [{i+1}s] unexpected: {body}", flush=True)
            break
    else:
        print("       Timeout waiting for completion", flush=True)

    # ---- 5. RESULT ----
    print("\n[5] Analysis Result", flush=True)
    code, body = req("GET", f"/analysis/{job_id}/result")
    if check("GET /analysis/{job_id}/result", code, body):
        result = body.get("result_data", body.get("result", {}))
        summary = result.get("analysis_summary", {})
        print(f"       total_files={result.get('total_files')}", flush=True)
        print(f"       ui_files={summary.get('ui_files')}, logic_files={summary.get('logic_files')}, mixed={summary.get('mixed_files')}", flush=True)
        print(f"       project={result.get('project_name')}", flush=True)

    # ---- 6. DOWNLOAD ----
    print("\n[6] Download", flush=True)
    for fmt in ["json", "csv"]:
        dl_req = urllib.request.Request(
            BASE + f"/analysis/{job_id}/download?format={fmt}",
            headers={"Authorization": f"Bearer {token}"},
            method="GET"
        )
        try:
            resp = urllib.request.urlopen(dl_req, timeout=10)
            data = resp.read()
            print(f"  [OK] Download {fmt.upper()} - {len(data)} bytes", flush=True)
        except urllib.error.HTTPError as e:
            err_body = {}
            try:
                err_body = json.loads(e.read())
            except:
                pass
            check(f"Download {fmt.upper()}", e.code, err_body)

# ---- 7. HISTORY ----
print("\n[7] History", flush=True)
code, body = req("GET", "/analysis/history")
if check("GET /analysis/history", code, body):
    if isinstance(body, list):
        print(f"       {len(body)} jobs in history", flush=True)
    elif isinstance(body, dict):
        items = body.get("items", body.get("jobs", []))
        print(f"       {len(items)} jobs in history", flush=True)

print("\n" + "=" * 55, flush=True)
print("  Test Complete!", flush=True)
print("=" * 55, flush=True)
