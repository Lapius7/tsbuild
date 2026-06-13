import locale
import os
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
def bar():  return c("  " + "─" * 52, GRAY)
def dbar(): return c("  " + "═" * 52, GRAY)


# ── i18n ──────────────────────────────────────────────────────────

def _detect_lang(override: Optional[str] = None) -> str:
    if override in ("ja", "en"):
        return override
    env = os.environ.get("TSBUILD_LANG", "")
    if env in ("ja", "en"):
        return env
    try:
        loc = locale.getdefaultlocale()[0] or ""
        return "ja" if loc.startswith("ja") else "en"
    except Exception:
        return "en"


T: dict = {
    "ja": {
        "tagline":    "Bun + TypeScript 開発サーバーをホットリロード付きで1コマンド起動",
        "author":     "開発者",
        "ver_ok":     "✓ 最新です",
        "ver_fail":   "(バージョン確認失敗)",
        "ver_new":    "↑ v{} が利用可能",
        "update":     "  ↑ 新バージョン v{} があります — pip install --upgrade tsbuild",
        "guide":      "使い方",
        "help":       "ヘルプ",
        "usage":      "使い方",
        "usage_cmd":  "tsbuild [オプション]",
        "desc":       "tssetup で作成したプロジェクトのルートで実行してください",
        "opts":       "オプション",
        "o_ver":      "バージョンを表示",
        "o_help":     "このヘルプを表示",
        "o_lang":     "表示言語",
        "what_title": "起動時の動作",
        "what_1":     "空きポートを 53000 番から自動探索してサーバーを起動",
        "what_2":     "初回 TypeScript コンパイルを実行（ブラウザ起動前に JS を生成）",
        "what_3":     "ブラウザで開発サーバーを自動起動",
        "what_4":     "tsc --watch でファイル変更を監視・自動コンパイル",
        "what_5":     "WebSocket 経由でブラウザをホットリロード",
        "req_title":  "必要なファイル",
        "req_1":      "package.json",
        "req_2":      "server.ts",
        "req_note":   "tssetup で作成したプロジェクトなら自動的に揃っています",
        "stop":       "Ctrl+C で停止",
        "examples":   "例",
        "compiling":  "▶ TypeScript コンパイル中...",
        "compile_ok": "完了",
        "compile_err":"失敗",
        "server_up":  "▶ 開発サーバー起動          ",
        "browser":    "▶ ブラウザを起動中...",
        "browser_ok": "完了",
        "hotreload":  "🔥 ホットリロード稼働中",
        "stop_hint":  "Ctrl+C で停止",
        "stopping":   "🛑 停止しています...",
        "stopped":    "✓ 終了しました",
    },
    "en": {
        "tagline":    "Launch a Bun + TypeScript dev server with hot-reload in one command",
        "author":     "Author",
        "ver_ok":     "✓ up to date",
        "ver_fail":   "(version check failed)",
        "ver_new":    "↑ v{} available",
        "update":     "  ↑ New version v{} available — pip install --upgrade tsbuild",
        "guide":      "Guide",
        "help":       "Help",
        "usage":      "Usage",
        "usage_cmd":  "tsbuild [options]",
        "desc":       "Run in the root of a project created with tssetup",
        "opts":       "Options",
        "o_ver":      "Show version",
        "o_help":     "Show this help",
        "o_lang":     "Display language",
        "what_title": "What it does",
        "what_1":     "Scans for a free port starting from 53000 and starts the server",
        "what_2":     "Runs an initial TypeScript compile before opening the browser",
        "what_3":     "Opens the dev server in your default browser",
        "what_4":     "Watches for file changes with tsc --watch",
        "what_5":     "Hot-reloads the browser via WebSocket on rebuild",
        "req_title":  "Required files",
        "req_1":      "package.json",
        "req_2":      "server.ts",
        "req_note":   "Both are generated automatically by tssetup",
        "stop":       "Press Ctrl+C to stop",
        "examples":   "Examples",
        "compiling":  "▶ Compiling TypeScript...",
        "compile_ok": "done",
        "compile_err":"failed",
        "server_up":  "▶ Dev server                ",
        "browser":    "▶ Opening browser...",
        "browser_ok": "done",
        "hotreload":  "🔥 Hot-reload active",
        "stop_hint":  "Press Ctrl+C to stop",
        "stopping":   "🛑 Stopping...",
        "stopped":    "✓ All processes terminated",
    },
}


# ── Version check ──────────────────────────────────────────────────

def fetch_remote_version() -> Optional[str]:
    try:
        url = "https://raw.githubusercontent.com/Lapius7/tsbuild/main/version.txt"
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def _ver_badge(remote: Optional[str], lang: str) -> str:
    s = T[lang]
    if remote is None:        return c(s["ver_fail"], GRAY)
    if remote == __version__: return c(s["ver_ok"], GREEN)
    return c(s["ver_new"].format(remote), YELLOW)


# ── Info screen ────────────────────────────────────────────────────

def show_info(remote: Optional[str], lang: str):
    s = T[lang]
    print()
    print(dbar())
    print(c("  ⚡  tsbuild  ", CYAN) + c(f"v{__version__}", WHITE)
          + "    " + _ver_badge(remote, lang))
    print(dbar())
    print(f"\n  {c(s['tagline'], GRAY)}\n")
    W = 10
    print(f"  {c((s['author']+' ').ljust(W), GRAY)}Lapius7")
    print(f"  {c('X'.ljust(W), GRAY)}https://x.com/Lapius7")
    print(f"  {c('GitHub'.ljust(W), GRAY)}https://github.com/Lapius7/tsbuild")
    print(f"  {c('PyPI'.ljust(W), GRAY)}https://pypi.org/project/tsbuild")
    print()
    print(f"  {c((s['guide']+' ').ljust(W), GRAY)}{s['usage_cmd']}")
    print(f"  {c((s['help']+' ').ljust(W), GRAY)}tsbuild --help")
    print()
    print(dbar())
    print()


# ── Custom help ────────────────────────────────────────────────────

def _opt(flags: str, desc: str, note: str = ""):
    f = c(f"  {flags:<22}", CYAN)
    d = c(desc, WHITE)
    n = c(f"  ({note})", GRAY) if note else ""
    print(f"{f}{d}{n}")

def _section(title: str):
    print(f"\n  {c(title, YELLOW)}")

def _bullet(text: str):
    print(f"    {c('·', GRAY)} {c(text, WHITE)}")

def show_help(lang: str):
    s = T[lang]
    print()
    print(dbar())
    print(c("  ⚡  tsbuild  ", CYAN) + c(f"v{__version__}", WHITE))
    print(c(f"  {s['tagline']}", GRAY))
    print(dbar())

    _section(s["usage"])
    print(f"    {c(s['usage_cmd'], WHITE)}")
    print(f"    {c(s['desc'], GRAY)}")

    _section(s["opts"])
    _opt("-v, --version",  s["o_ver"])
    _opt("-h, --help",     s["o_help"])
    _opt("    --lang",     s["o_lang"], "ja / en")

    _section(s["what_title"])
    for key in ["what_1","what_2","what_3","what_4","what_5"]:
        _bullet(s[key])

    _section(s["req_title"])
    print(f"    {c(s['req_1'], CYAN)}  {c(s['req_2'], CYAN)}")
    print(f"    {c(s['req_note'], GRAY)}")

    _section(s["examples"])
    print(f"    {c('tssetup my-app', WHITE)}   {c('# ' + ('プロジェクト作成' if lang=='ja' else 'create project'), GRAY)}")
    print(f"    {c('cd my-app', WHITE)}")
    print(f"    {c('tsbuild', WHITE)}           {c('# ' + ('開発サーバー起動' if lang=='ja' else 'start dev server'), GRAY)}")

    print()
    print(dbar())
    print()


# ── Dev server ─────────────────────────────────────────────────────

def run_server(lang: str):
    s = T[lang]

    if not Path("package.json").exists() or not Path("server.ts").exists():
        remote = fetch_remote_version()
        show_info(remote, lang)
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
        text=True, encoding="utf-8", errors="replace",
    )

    print(c(f"  {s['compiling']}", GRAY), end="", flush=True)
    tsc_result = subprocess.run(
        ["bun", "x", "tsc"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if tsc_result.returncode != 0:
        print(c(f"  {s['compile_err']}", RED))
        for line in (tsc_result.stdout + tsc_result.stderr).splitlines():
            if line.strip():
                print(c(f"    {line}", YELLOW))
    else:
        print(c(f"  {s['compile_ok']}", GREEN))

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

    print(c(f"  {s['server_up']}", GRAY) + c(target_url, CYAN))

    print(c(f"  {s['browser']}", GRAY), end="", flush=True)
    webbrowser.open(target_url)
    print(c(f"  {s['browser_ok']}", GREEN))

    print()
    print(bar())
    print(c(f"  {s['hotreload']}", GREEN))
    print(c(f"     {target_url}", CYAN))
    print(c(f"     {s['stop_hint']}", GRAY))
    print(bar())
    print()

    def cleanup(signum=None, frame=None):
        print()
        print(c(f"  {s['stopping']}", RED))
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print(c(f"  {s['stopped']}", GRAY))
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    try:
        subprocess.run(["bun", "x", "tsc", "--watch"])
    finally:
        cleanup()


# ── Entry point ────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(prog="tsbuild", add_help=False)
    parser.add_argument("--version", "-v", action="store_true")
    parser.add_argument("--help",    "-h", action="store_true")
    parser.add_argument("--lang",          default=None)
    args = parser.parse_args()

    lang = _detect_lang(args.lang)

    if args.version:
        print(f"tsbuild v{__version__}")
        return

    if args.help:
        show_help(lang)
        return

    remote = fetch_remote_version()
    if remote and remote != __version__:
        print()
        print(c(T[lang]["update"].format(remote), YELLOW))

    run_server(lang)


if __name__ == "__main__":
    main()
