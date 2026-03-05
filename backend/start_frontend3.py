"""Start the frontend dev server as a detached process"""
import subprocess
import os
import sys

# Fix stdout encoding for Korean Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
print(f"Frontend dir: {frontend_dir}", flush=True)

# Start npm run dev as a completely detached Windows process
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'
env['FORCE_COLOR'] = '0'  # Disable color codes

try:
    proc = subprocess.Popen(
        ['npm.cmd', 'run', 'dev'],
        cwd=frontend_dir,
        env=env,
        # No stdout/stderr capture - let it run independently
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # Detach from parent process group on Windows
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
        close_fds=True
    )

    print(f"Frontend process started! PID: {proc.pid}", flush=True)
    print("Waiting for Vite to start...", flush=True)

    # Read a few lines to confirm startup
    import select
    import time
    start_time = time.time()
    started = False

    while time.time() - start_time < 15:
        if proc.poll() is not None:
            print("Process exited early!", flush=True)
            break

        try:
            line = proc.stdout.readline()
            if line:
                decoded = line.decode('utf-8', errors='replace').rstrip()
                # Strip ANSI color codes for display
                import re
                clean = re.sub(r'\x1b\[[0-9;]*m', '', decoded)
                print(f"  {clean}", flush=True)
                if 'ready in' in clean or 'Local:' in clean or 'Network:' in clean:
                    started = True
                if started and 'Local:' in clean:
                    break
        except Exception as e:
            print(f"Read error: {e}", flush=True)
            break

    if started:
        print("\nFrontend is running!", flush=True)
    else:
        print("\nFrontend may be running (check port 5173 or nearby)", flush=True)

    print(f"Frontend PID: {proc.pid} (keep this running)", flush=True)
    # Don't wait - detach the process
    proc.stdout.close()

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
