import sys
import subprocess
import urllib.request
import webbrowser
import re
import time
import signal
import threading
from pathlib import Path
from typing import Optional

from . import __version__

def _setup_console():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(
                ctypes.windll.kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_setup_console()

R      = "\033[0m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"
RED    = "\033[31m"

def c(text, color): return f"{color}{text}{R}"
def bar(): return c("  " + "─" * 44, GRAY)


def fetch_remote_version() -> Optional[str]:
    try:
        url = "https://raw.githubusercontent.com/Lapius7/tsbuild/main/version.txt"
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def show_info(remote: Optional[str]):
    if remote is None:
        status = c("(バージョン確認失敗)", GRAY)
    elif remote == __version__:
        status = c("✓ 最新です", GREEN)
    else:
        status = c(f"↑ v{remote} が利用可能", YELLOW)

    print()
    print(c("  tsbuild", CYAN) + c(f" v{__version__}  ", GRAY) + status)
    print(c("  Bun + TypeScript 開発サーバーをホットリロード付きで1コマンド起動", GRAY))
    print()
    print(c("  開発者  ", GRAY) + "Lapius7")
    print(c("  X       ", GRAY) + "https://x.com/Lapius7")
    print(c("  GitHub  ", GRAY) + "https://github.com/Lapius7/tsbuild")
    print()
    print(c("  使い方  tssetup でプロジェクトを作成し、そのフォルダ内で tsbuild を実行", GRAY))
    print(c("  ヘルプ  tsbuild --help", GRAY))
    print()


def run_server():
    if not Path("package.json").exists() or not Path("server.ts").exists():
        remote = fetch_remote_version()
        show_info(remote)
        return

    print()
    print(bar())
    print(c("  ⚡ tsbuild", CYAN))
    print(bar())
    print()

    server_proc = subprocess.Popen(
        ["bun", "server.ts"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Initial compile
    print(c("  ▶ TypeScript コンパイル中...", GRAY), end="", flush=True)
    tsc_result = subprocess.run(
        ["bun", "x", "tsc"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if tsc_result.returncode != 0:
        print(c("  失敗", RED))
        for line in (tsc_result.stdout + tsc_result.stderr).splitlines():
            if line.strip():
                print(c(f"    {line}", YELLOW))
    else:
        print(c("  完了", GREEN))

    # Detect server URL
    target_url = "http://localhost:53000"
    deadline = time.time() + 5

    def _read_url():
        nonlocal target_url
        while time.time() < deadline:
            line = server_proc.stdout.readline()
            if not line:
                break
            m = re.search(r"http://localhost:\d+", line)
            if m:
                target_url = m.group()
                break

    t = threading.Thread(target=_read_url, daemon=True)
    t.start()
    t.join(timeout=5)

    print(c("  ▶ 開発サーバー           ", GRAY) + c(target_url, CYAN))

    print(c("  ▶ ブラウザを起動中...", GRAY), end="", flush=True)
    webbrowser.open(target_url)
    print(c("  完了", GREEN))

    print()
    print(bar())
    print(c("  🔥 ホットリロード稼働中", GREEN))
    print(c(f"     {target_url}", CYAN))
    print(c("     Ctrl+C で停止", GRAY))
    print(bar())
    print()

    def cleanup(signum=None, frame=None):
        print()
        print(c("  🛑 停止しています...", RED))
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print(c("  ✓ 終了しました", GRAY))
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    try:
        subprocess.run(["bun", "x", "tsc", "--watch"])
    finally:
        cleanup()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog="tsbuild",
        description="Bun + TypeScript 開発サーバーをホットリロード付きで起動するツール",
    )
    parser.add_argument("--version", "-v", action="store_true", help="バージョンを表示")
    args = parser.parse_args()

    if args.version:
        print(f"tsbuild v{__version__}")
        return

    remote = fetch_remote_version()
    if remote and remote != __version__:
        print()
        print(c(f"  ↑ 新バージョン v{remote} があります  pip install --upgrade tsbuild", YELLOW))

    run_server()


if __name__ == "__main__":
    main()
