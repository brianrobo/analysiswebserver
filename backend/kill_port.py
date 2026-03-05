"""Kill ALL processes using port 8000"""
import subprocess
import sys

try:
    # Get PID using port 8000
    result = subprocess.run(
        ['netstat', '-ano'],
        capture_output=True, text=True, encoding='cp949', errors='replace'
    )

    pids = set()
    for line in result.stdout.splitlines():
        if ':8000 ' in line and 'LISTENING' in line:
            parts = line.split()
            if parts:
                pid = parts[-1]
                if pid and pid != '0':
                    pids.add(pid)

    print(f"Found PIDs on port 8000: {pids}", flush=True)

    for pid in pids:
        print(f"Killing PID {pid}...", flush=True)
        kill_result = subprocess.run(['taskkill', '/F', '/PID', pid],
                                     capture_output=True, text=True, encoding='cp949', errors='replace')
        print(f"  Result: {kill_result.stdout.strip()} {kill_result.stderr.strip()}", flush=True)

    if not pids:
        print("No processes found on port 8000", flush=True)

except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Done", flush=True)
