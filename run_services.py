import os
import signal
import subprocess
import sys
import time
from typing import List

processes: List[subprocess.Popen] = []


def start_process(command: List[str]) -> subprocess.Popen:
    process = subprocess.Popen(command)
    processes.append(process)
    return process


def terminate_processes():
    for process in processes:
        if process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass


def signal_handler(signum, frame):
    terminate_processes()
    sys.exit(0)


def run():
    app_port = os.getenv("APP_PORT", "8000")
    uvicorn_cmd = [
        "uvicorn",
        "app:app",
        "--host",
        "0.0.0.0",
        "--port",
        app_port,
    ]
    if os.getenv("UVICORN_RELOAD") == "1":
        uvicorn_cmd.append("--reload")

    start_process(uvicorn_cmd)
    start_process([sys.executable, "MCP/mcp_server.py"])

    while True:
        for process in list(processes):
            return_code = process.poll()
            if return_code is not None:
                terminate_processes()
                return return_code
        time.sleep(0.5)


def main() -> int:
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        exit_code = run()
    except KeyboardInterrupt:
        terminate_processes()
        exit_code = 0
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
