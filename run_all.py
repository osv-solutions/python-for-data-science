"""Run every script in the companion repository and report the ones that fail.

Scripts that ask for keyboard input are fed the answers used in the book,
from the matching <name>.inputs.txt file. Scripts that expect the practice
server to be running in another terminal, such as Project 10's pipeline.py,
get one for the length of their run.

With pytest installed, the tests in examples/ run too.

Usage:  python run_all.py            (all scripts)
        python run_all.py ch03       (only scripts whose path contains "ch03")
"""
import importlib.util
import pathlib
import socket
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent


def scripts(pattern=""):
    for folder in ("chapters", "projects", "solutions"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            if ("_snippet" in path.name or path.name == "practice_web.py"
                    or pattern not in str(path)):
                continue
            yield path


def start_server(folder):
    server = subprocess.Popen([sys.executable, "practice_web.py"],
                              cwd=folder, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            socket.create_connection(("127.0.0.1", 8020), 1).close()
            break
        except OSError:
            time.sleep(0.25)
    return server


def run(path):
    inputs = path.with_suffix(".inputs.txt")
    stdin = inputs.read_text(encoding="utf-8") if inputs.exists() else ""
    code = path.read_text(encoding="utf-8")
    server = None
    if "practice_web.py in another terminal" in code:
        server = start_server(path.parent)
    try:
        result = subprocess.run([sys.executable, path.name],
                                cwd=path.parent, input=stdin,
                                capture_output=True, text=True,
                                timeout=900)
    finally:
        if server:
            server.terminate()
            server.wait()
    return result.returncode, result.stderr


def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else ""
    failed = []
    for path in scripts(pattern):
        code, err = run(path)
        name = path.relative_to(ROOT)
        print(f"{'ok  ' if code == 0 else 'FAIL'} {name}")
        if code != 0:
            failed.append((name, err))
    if not pattern and importlib.util.find_spec("pytest"):
        for folder in sorted((ROOT / "examples").glob("*")):
            if not any(folder.rglob("test_*.py")):
                continue
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                cwd=folder, capture_output=True, text=True, timeout=900)
            name = folder.relative_to(ROOT)
            print(f"{'ok  ' if result.returncode == 0 else 'FAIL'} {name} (pytest)")
            if result.returncode != 0:
                failed.append((name, result.stdout))
    for name, err in failed:
        print(f"\n--- {name}\n{err[-2000:]}")
    print(f"\n{len(failed)} failed" if failed else "\nAll scripts ran successfully.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
