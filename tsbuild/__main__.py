import sys
import subprocess
import urllib.request
import webbrowser
import re
import time
import signal
import threading
from pathlib import Path

from . import __version__

# --- Console setup (Windows: enable ANSI + force UTF-8) ---

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

R = "\033[0m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"
RED    = "\033[31m"

def c(text, color): return f"{color}{text}{R}"


# --- Version check ---

def fetch_remote_version() -> str | None:
    try:
        url = "https://raw.githubusercontent.com/Lapius7/tsbuild/main/version.txt"
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.read().decode().strip()
    except Exception:
        return None


# --- Info screen ---

def show_info(remote: str | None):
    print()
    print(c("⚡ tsbuild", CYAN) + c(f"  v{__version__}", GRAY))
    print("Bun + TypeScript 開発サーバーをホットリロード付きで1コマンド起動するツール")
    print()
    print(c("開発者  : ", YELLOW) + "Lapius7")
    print(c("X       : ", YELLOW) + "https://x.com/Lapius7")
    print(c("GitHub  : ", YELLOW) + "https://github.com/Lapius7/tsbuild")
    print()
    if remote is None:
        print(f"バージョン  : {__version__}  " + c("(バージョン確認失敗)", GRAY))
    elif remote == __version__:
        print(f"バージョン  : {__version__}  " + c("✅ 最新です", GREEN))
    else:
        print(f"バージョン  : {__version__}  " + c(f"⬆ 最新: {remote}", YELLOW))
    print()
    print(c("使い方  : tssetup でプロジェクトを作成してから、そのフォルダ内で tsbuild を実行してください", GRAY))
    print(c("ヘルプ  : tsbuild --help", GRAY))
    print()


# --- Dev server ---

def run_server():
    if not Path("package.json").exists() or not Path("server.ts").exists():
        remote = fetch_remote_version()
        show_info(remote)
        return

    print(c("🚀 開発環境を起動中（ホットリロード有効）...", CYAN))

    server_proc = subprocess.Popen(
        ["bun", "server.ts"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Initial compile
    tsc_result = subprocess.run(
        ["bun", "x", "tsc"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if tsc_result.returncode != 0:
        print(c("⚠ TypeScript コンパイルエラー:", YELLOW))
        for line in (tsc_result.stdout + tsc_result.stderr).splitlines():
            print(c(f"  {line}", YELLOW))

    # Wait for server URL
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

    webbrowser.open(target_url)

    print(c("=" * 50, YELLOW))
    print(c(" 🔥 ホットリロード稼働中！コードを変更するとブラウザが自動更新されます。", GREEN))
    print(c(" [Ctrl + C] を押すと、すべてのプロセスを終了します。", YELLOW))
    print(c("=" * 50, YELLOW))

    def cleanup(signum=None, frame=None):
        print(c("\n🛑 開発環境を停止しています...", RED))
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print(c("✨ すべてのプロセスが正常に終了しました。", GREEN))
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    try:
        subprocess.run(["bun", "x", "tsc", "--watch"])
    finally:
        cleanup()


# --- Entry point ---

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
        print(c(f"🔄 新しいバージョン ({remote}) があります。pip install --upgrade tsbuild で更新できます。", YELLOW))

    run_server()


if __name__ == "__main__":
    main()
