#!/usr/bin/env python3
"""ALNUA Hub supervisor — one parent process for API + Web (replaces PS watchdogs)."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
WEB = ROOT / "web"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
LOCK = DATA / "hub.supervisor.lock"
STATE = DATA / "hub.supervisor.json"
LOG = DATA / "hub_supervisor.log"
API_LOG = DATA / "hub_uvicorn.log"
WEB_LOG = DATA / "hub_web.log"
PORT_FILE = DATA / "hub_active_port.txt"

DEFAULT_API_PORT = 8003
DEFAULT_WEB_PORT = 3000
BOOT_GRACE_S = 90
WEB_BOOT_GRACE_S = 120
CHECK_INTERVAL_S = 15
MAX_FAILS_BEFORE_RESTART = 5
WEB_MAX_FAILS_BEFORE_RESTART = 3
HEALTH_TIMEOUT_S = 12.0
HEALTH_RETRIES = 3
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def _no_window() -> dict:
    """Hide console flashes on Windows (powershell/cmd/taskkill children)."""
    if sys.platform != "win32":
        return {}
    return {"creationflags": CREATE_NO_WINDOW}


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    kw = {**_no_window(), **kwargs}
    return subprocess.run(cmd, **kw)


def _run_ps(command: str) -> subprocess.CompletedProcess:
    return _run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
    )


def log(msg: str) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def read_state() -> dict:
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_state(data: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_port(port: int) -> None:
    PORT_FILE.write_text(str(port), encoding="ascii")


def _env_get(path: Path, name: str) -> str:
    if not path.exists():
        return ""
    prefix = f"{name}="
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1].strip()
    return ""


def _env_set_lines(lines: list[str], name: str, value: str) -> list[str]:
    prefix = f"{name}="
    out = list(lines)
    for i, line in enumerate(out):
        if line.startswith(prefix):
            out[i] = f"{name}={value}"
            return out
    out.append(f"{name}={value}")
    return out


def sync_web_env(api_port: int) -> None:
    """Mirror HUB_API_* into web/.env.local without spawning PowerShell."""
    write_port(api_port)
    web_env = WEB / ".env.local"
    root_env = ROOT / ".env"
    hub_key = _env_get(root_env, "HUB_API_KEY")
    backend_url = f"http://127.0.0.1:{api_port}"
    if web_env.exists():
        lines = web_env.read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        example = WEB / ".env.example"
        lines = (
            example.read_text(encoding="utf-8", errors="replace").splitlines()
            if example.exists()
            else []
        )
    lines = _env_set_lines(lines, "HUB_API_BACKEND_URL", backend_url)
    if hub_key:
        lines = _env_set_lines(lines, "HUB_API_KEY", hub_key)
    web_env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"Sync OK: HUB_API_BACKEND_URL={backend_url}")


def health_ok(port: int, timeout: float = HEALTH_TIMEOUT_S) -> bool:
    for attempt in range(HEALTH_RETRIES):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/health")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
                if body.get("service") == "alnua-hub":
                    return True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            if attempt < HEALTH_RETRIES - 1:
                time.sleep(2)
    return False


def port_open(port: int, timeout: float = 2.0) -> bool:
    import socket

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def web_ok(port: int, timeout: float = 8.0) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":
        r = _run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
        )
        return str(pid) in (r.stdout or "")
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_tree(pid: int | None) -> None:
    if not pid or pid <= 0:
        return
    if sys.platform == "win32":
        _run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
        )
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def kill_supervisor_orphans(keep_pid: int | None = None) -> None:
    if sys.platform != "win32":
        return
    keep = int(keep_pid or 0)
    _run_ps(
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -match 'hub_supervisor\\.py run' } | "
        f"Where-Object {{ $_.ProcessId -ne {keep} }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )


def owns_lock() -> bool:
    if not LOCK.exists():
        return False
    try:
        return int(LOCK.read_text(encoding="ascii").strip()) == os.getpid()
    except (ValueError, OSError):
        return False


def kill_uvicorn_orphans() -> None:
    if sys.platform != "win32":
        return
    _run_ps(
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -match 'uvicorn api\\.main' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )


def hub_env() -> dict[str, str]:
    env = os.environ.copy()
    env["TELEGRAM_POLLING"] = "0"
    env["TELEGRAM_SECRETARY_POLLING"] = "0"
    env["HUB_FAST_START"] = "1"
    return env


def start_api(port: int, *, cleanup_orphans: bool = False) -> subprocess.Popen:
    if cleanup_orphans:
        kill_uvicorn_orphans()
    DATA.mkdir(parents=True, exist_ok=True)
    log_file = API_LOG.open("a", encoding="utf-8")
    proc = subprocess.Popen(
        [
            str(VENV_PY),
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "info",
            "--limit-concurrency",
            "40",
            "--timeout-keep-alive",
            "5",
        ],
        cwd=str(ROOT),
        env=hub_env(),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=CREATE_NO_WINDOW,
    )
    log(f"API demarre PID {proc.pid} -> http://127.0.0.1:{port}")
    return proc


def wait_api(port: int, max_wait_s: int = 120) -> bool:
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        if health_ok(port, timeout=10.0):
            log(f"API pret sur :{port}")
            return True
        time.sleep(2)
    log(f"API pas pret apres {max_wait_s}s")
    return False


def free_port(port: int) -> None:
    if sys.platform != "win32":
        return
    _run_ps(
        f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
        "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
    )


def start_web(port: int) -> subprocess.Popen:
    """Start Next without npx.cmd (cmd.exe flashes a console even with CREATE_NO_WINDOW)."""
    DATA.mkdir(parents=True, exist_ok=True)
    log_file = WEB_LOG.open("a", encoding="utf-8")
    next_cli = WEB / "node_modules" / "next" / "dist" / "bin" / "next"
    node = "node.exe" if sys.platform == "win32" else "node"
    if next_cli.exists():
        cmd = [node, str(next_cli), "dev", "-p", str(port)]
    else:
        # Fallback — still hide the console
        npx = "npx.cmd" if sys.platform == "win32" else "npx"
        cmd = [npx, "next", "dev", "-p", str(port)]
    proc = subprocess.Popen(
        cmd,
        cwd=str(WEB),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        **_no_window(),
    )
    log(f"Web demarre PID {proc.pid} -> http://localhost:{port}")
    return proc


def wait_web(port: int, max_wait_s: int = WEB_BOOT_GRACE_S) -> bool:
    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        if web_ok(port):
            log(f"Web pret sur :{port}")
            return True
        time.sleep(2)
    log(f"Web pas pret apres {max_wait_s}s")
    return False


def restart_web(port: int, web_proc: subprocess.Popen | None) -> subprocess.Popen:
    if web_proc and web_proc.poll() is None:
        kill_tree(web_proc.pid)
    free_port(port)
    time.sleep(2)
    return start_web(port)


def stop_all() -> None:
    state = read_state()
    my_pid = os.getpid()
    sup_pid = state.get("supervisor_pid")
    kill_supervisor_orphans(keep_pid=my_pid)
    if sup_pid and sup_pid != my_pid and _alive(sup_pid):
        kill_tree(sup_pid)
        time.sleep(1)
    for key in ("api_pid", "web_pid"):
        kill_tree(state.get(key))
    free_port(int(state.get("web_port") or DEFAULT_WEB_PORT))
    kill_uvicorn_orphans()
    for path in (LOCK, STATE):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    log("Supervisor arrete")


def cmd_stop(_: argparse.Namespace) -> int:
    stop_all()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = read_state()
    api_port = int(state.get("api_port") or args.api_port)
    web_port = int(state.get("web_port") or args.web_port)
    print(f"API  : {'OK' if health_ok(api_port) else 'DOWN'} (:{api_port}, pid={state.get('api_pid')})")
    print(f"Web  : {'OK' if web_ok(web_port) else 'DOWN'} (:{web_port}, pid={state.get('web_pid')})")
    print(f"Lock : {'present' if LOCK.exists() else 'absent'}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not VENV_PY.exists():
        log(f"venv introuvable: {VENV_PY}")
        return 1

    if LOCK.exists():
        old = read_state()
        if old.get("supervisor_pid") and _alive(old.get("supervisor_pid")):
            if health_ok(args.api_port):
                log("Supervisor deja actif")
                return 0
        stop_all()

    DATA.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(str(os.getpid()), encoding="ascii")
    sync_web_env(args.api_port)
    write_port(args.api_port)

    api_proc: subprocess.Popen | None = None
    web_proc: subprocess.Popen | None = None
    api_started_at = 0.0
    web_started_at = 0.0
    api_fail_streak = 0
    web_fail_streak = 0

    def persist() -> None:
        write_state(
            {
                "supervisor_pid": os.getpid(),
                "api_pid": api_proc.pid if api_proc else None,
                "web_pid": web_proc.pid if web_proc else None,
                "api_port": args.api_port,
                "web_port": args.web_port,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    log(f"=== Supervisor demarre (PID {os.getpid()}) ===")

    if args.skip_web:
        api_proc = start_api(args.api_port, cleanup_orphans=True)
        api_started_at = time.time()
        if not wait_api(args.api_port):
            kill_tree(api_proc.pid)
            stop_all()
            return 1
        persist()
        log("Mode API seul — Ctrl+C pour arreter")
        try:
            while True:
                time.sleep(CHECK_INTERVAL_S)
                if api_proc.poll() is not None:
                    log("API terminee — redemarrage")
                    kill_tree(api_proc.pid)
                    time.sleep(1)
                    api_proc = start_api(args.api_port)
                    api_started_at = time.time()
                    wait_api(args.api_port, max_wait_s=BOOT_GRACE_S)
                    persist()
        except KeyboardInterrupt:
            stop_all()
        return 0

    api_proc = start_api(args.api_port, cleanup_orphans=True)
    api_started_at = time.time()
    if not wait_api(args.api_port):
        kill_tree(api_proc.pid)
        stop_all()
        return 1

    web_proc = start_web(args.web_port)
    web_started_at = time.time()
    wait_web(args.web_port)
    persist()

    try:
        while True:
            if not owns_lock():
                log("Lock perdu — arret de ce superviseur")
                kill_tree(api_proc.pid if api_proc else None)
                kill_tree(web_proc.pid if web_proc else None)
                return 0
            time.sleep(CHECK_INTERVAL_S)
            now = time.time()
            api_in_grace = (now - api_started_at) < BOOT_GRACE_S
            web_in_grace = (now - web_started_at) < WEB_BOOT_GRACE_S

            if api_proc.poll() is not None:
                log(f"API exit code {api_proc.returncode} — redemarrage")
                kill_tree(api_proc.pid)
                time.sleep(1)
                api_proc = start_api(args.api_port)
                api_started_at = time.time()
                api_fail_streak = 0
                wait_api(args.api_port, max_wait_s=BOOT_GRACE_S)
                persist()
                continue

            if not health_ok(args.api_port):
                if api_in_grace:
                    continue
                api_fail_streak += 1
                log(f"API health KO ({api_fail_streak}/{MAX_FAILS_BEFORE_RESTART})")
                dead_socket = not port_open(args.api_port)
                if dead_socket:
                    log("Recycle API (port ferme)")
                    kill_tree(api_proc.pid)
                    time.sleep(1)
                    api_proc = start_api(args.api_port)
                    api_started_at = time.time()
                    api_fail_streak = 0
                    wait_api(args.api_port, max_wait_s=BOOT_GRACE_S)
                    persist()
                elif api_fail_streak >= MAX_FAILS_BEFORE_RESTART:
                    log("Recycle API (health KO repete — API bloquee)")
                    kill_tree(api_proc.pid)
                    time.sleep(1)
                    api_proc = start_api(args.api_port)
                    api_started_at = time.time()
                    api_fail_streak = 0
                    wait_api(args.api_port, max_wait_s=BOOT_GRACE_S)
                    persist()
            else:
                api_fail_streak = 0

            if web_proc.poll() is not None:
                if web_ok(args.web_port):
                    log(
                        f"Web wrapper termine (code {web_proc.returncode}) — "
                        "serveur Next.js encore actif"
                    )
                else:
                    log(f"Web exit code {web_proc.returncode} — redemarrage")
                    web_proc = restart_web(args.web_port, web_proc)
                    web_started_at = time.time()
                    wait_web(args.web_port)
                    persist()
            elif not web_ok(args.web_port):
                if web_in_grace:
                    continue
                web_fail_streak += 1
                log(f"Web health KO ({web_fail_streak}/{WEB_MAX_FAILS_BEFORE_RESTART})")
                if web_fail_streak >= WEB_MAX_FAILS_BEFORE_RESTART:
                    log("Web KO — redemarrage")
                    web_proc = restart_web(args.web_port, web_proc)
                    web_started_at = time.time()
                    web_fail_streak = 0
                    wait_web(args.web_port)
                    persist()
            else:
                web_fail_streak = 0

    except KeyboardInterrupt:
        log("Interruption — arret propre")
        stop_all()
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Start supervisor detached (for Demarrer-Hub.bat)."""
    if LOCK.exists():
        state = read_state()
        if state.get("supervisor_pid") and _alive(state.get("supervisor_pid")):
            if health_ok(args.api_port):
                log("Deja en marche")
                return 0
        stop_all()

    kill_supervisor_orphans()
    py = str(VENV_PY)
    script = str(Path(__file__).resolve())
    cmd = [py, script, "run", "--api-port", str(args.api_port), "--web-port", str(args.web_port)]
    if args.skip_web:
        cmd.append("--skip-web")
    if sys.platform == "win32":
        # Prefer pythonw so the detached supervisor has no console at all
        pyw = ROOT / ".venv" / "Scripts" / "pythonw.exe"
        launch = [str(pyw if pyw.exists() else VENV_PY), *cmd[1:]]
        subprocess.Popen(
            launch,
            cwd=str(ROOT),
            close_fds=True,
            **_no_window(),
        )
    else:
        subprocess.Popen(cmd, cwd=str(ROOT), start_new_session=True, close_fds=True)
    log("Supervisor lance en arriere-plan")
    for _ in range(60):
        time.sleep(2)
        if health_ok(args.api_port):
            log("API OK")
            return 0
    log("API pas encore pret — le supervisor continue en arriere-plan")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ALNUA Hub supervisor")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name, fn in (
        ("start", cmd_start),
        ("run", cmd_run),
        ("stop", cmd_stop),
        ("status", cmd_status),
    ):
        p = sub.add_parser(name)
        p.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
        p.add_argument("--web-port", type=int, default=DEFAULT_WEB_PORT)
        p.add_argument("--skip-web", action="store_true")
        p.set_defaults(func=fn)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
