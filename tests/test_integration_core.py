import subprocess
import sys
import time

def test_core_main_runs():
    # Start the backend as a module
    proc = subprocess.Popen([sys.executable, '-m', 'core.core'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        # Wait for 'ready' message in stdout
        start = time.time()
        ready = False
        while time.time() - start < 10:
            line = proc.stdout.readline()
            if not line:
                continue
            if 'ready' in line:
                ready = True
                break
        assert ready, "Did not receive 'ready' signal from core.core."
        # Send shutdown message
        proc.stdin.write('{"type": "shutdown"}\n')
        proc.stdin.flush()
        proc.stdin.close()
        proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.terminate()
    assert proc.returncode == 0, f"core.core exited with code {proc.returncode}. Output: {proc.stdout.read()}\nErrors: {proc.stderr.read()}"

if __name__ == "__main__":
    test_core_main_runs()
    print("Integration test passed: core.core runs and shuts down without error.")
