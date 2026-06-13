# tsbuild

`tssetup` で構築した Bun + TypeScript プロジェクトにおいて、開発サーバーの起動・TypeScript の自動ビルド・ブラウザのホットリロードを1コマンドで一元管理する開発支援ツールです。

## 🚀 特徴

- **1コマンド起動:** ローカルWebサーバー起動・ブラウザ自動起動・TS監視ビルドをすべて開始します。
- **ポート衝突の自動回避:** デフォルトの 53000 番ポートが使用中の場合、空いているポートを自動で探します。
- **404エラー防止:** 起動と同時に初回コンパイルを実行し、ブラウザ起動直後の404エラーを防ぎます。
- **ホットリロード:** `src/` 内のコード変更や `index.html` の編集を検知し、ブラウザを自動でリロードします。
- **ゾンビプロセス防止:** `Ctrl + C` で終了した際に、バックグラウンドの Bun サーバーを自動停止・クリーンアップします。
- **自動バージョン確認:** 実行時に最新バージョンを確認し、更新がある場合は通知します。

---

## 🛠️ インストール方法

```bash
pip install tsbuild
```

> [!NOTE]
>
> - PowerShell・CMD・Windows Terminal どれからでも使えます。
> - 動作には **Python 3.9+** と **Bun** が必要です。

---

## ⚙️ 動作に必要な環境（依存関係）

| ツール | 用途 | インストール |
| :--- | :--- | :--- |
| **Python 3.9+** | tsbuild 本体の実行 | [python.org](https://www.python.org/) |
| **Bun** | 開発サーバー起動・TSコンパイル | `powershell -c "irm bun.sh/install.ps1 \| iex"` |

---

## ⚡ 使い方

`tssetup` で構築したプロジェクトのルートディレクトリ（`package.json` と `server.ts` があるフォルダ）で実行します。

```bash
tsbuild
```

プロジェクト外（`package.json` / `server.ts` がないディレクトリ）で実行するとバージョン情報・インフォ画面が表示されます。

### パラメータ

| パラメータ | 短縮形 | 説明 |
| :--- | :--- | :--- |
| `--version` | `-v` | バージョンを表示 |
| `--help` | `-h` | ヘルプを表示 |

---

## 📁 対象プロジェクトの構成

`tsbuild` は `tssetup` で作成した以下の構成を前提としています。

```
my-app/
├── src/
│   └── index.ts        ← 編集対象の TypeScript ファイル
├── dist/               ← tsc が自動生成する JS 出力先
├── index.html          ← フロントエンドの HTML
├── server.ts           ← tsbuild が起動する Bun サーバー
├── tsconfig.json       ← TypeScript コンパイラ設定
└── package.json        ← Bun プロジェクト設定
```

---

## 🚀 プロジェクトの始め方

```bash
# 1. プロジェクトを作成（カレントディレクトリが自動で移動）
tssetup my-app

# 2. 開発サーバーを起動
tsbuild
```

---

## コマンド実行時の挙動

1. **ポート自動探索** — `53000` 番から順に空きポートを検索してサーバーを起動
2. **初回ビルド** — `bun x tsc` で初回コンパイルを実行（ブラウザ起動前に JS を生成）
3. **ブラウザ自動起動** — `http://localhost:53000`（または自動検出したポート）を開く
4. **リアルタイム監視** — `bun x tsc --watch` でファイル変更を検知して自動コンパイル
5. **ホットリロード** — ビルド完了後、WebSocket 経由でブラウザに通知してリロード

### 終了方法

**`Ctrl + C`** を押すと、バックグラウンドの Bun サーバーを自動停止してクリーンアップします。

---

## 🔄 アップデート

```bash
pip install --upgrade tsbuild
```

---

## ✉️ 問い合わせ先

- **X (旧Twitter):** [@Lapius7](https://x.com/Lapius7)
- **GitHub Issues:** [Lapius7/tsbuild/issues](https://github.com/Lapius7/tsbuild/issues)

---

## ⚠️ 免責事項

本ソフトウェアの使用によって生じた直接的・間接的な損害について、作者は一切の責任を負いません。自己責任のもとでご使用ください。

---

## 📄 ライセンス & コピーライト

本プロジェクトは [MIT License](https://opensource.org/licenses/MIT) のもとで公開されています。

Copyright (c) 2026 Lapius7
