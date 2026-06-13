# 💡 インストールを実行するPowerShellスクリプト
$functionName = "tsbuild"
$functionCode = @'
function tsbuild {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)][switch]$Help,
        [Parameter(Mandatory = $false)][switch]$Uninstall
    )

    if ($Uninstall) {
        Write-Host ""
        Write-Host "⚠ tsbuild をアンインストールします。本当によろしいですか？ (y/N): " -NoNewline -ForegroundColor Yellow
        $confirm = Read-Host
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-Host "キャンセルしました。" -ForegroundColor DarkGray
            return
        }
        $profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
        if ($profileContent -match "# <<BEGIN:tsbuild>>") {
            $profileContent = $profileContent -replace "(?s)`n?# <<BEGIN:tsbuild>>.*?# <<END:tsbuild>>", ""
            [System.IO.File]::WriteAllText($PROFILE, $profileContent.Trim(), [System.Text.UTF8Encoding]::new($true))
            Remove-Item Function:tsbuild -ErrorAction SilentlyContinue
            Write-Host "✅ tsbuild をアンインストールしました。" -ForegroundColor Green
        } else {
            Write-Host "⚠ tsbuild はインストールされていません。" -ForegroundColor Yellow
        }
        return
    }

    $localVersion = "1.0.1"
    $remoteVersion = $null
    try {
        $remoteVersion = (irm https://raw.githubusercontent.com/Lapius7/tsbuild/main/version.txt -TimeoutSec 3 -ErrorAction Stop).Trim()
        if ($remoteVersion -ne $localVersion) {
            Write-Host "🔄 新しいバージョン ($remoteVersion) があります。自動更新しています..." -ForegroundColor Yellow
            irm https://raw.githubusercontent.com/Lapius7/tsbuild/main/install.ps1 | iex
            Write-Host "✅ 更新完了！もう一度コマンドを実行してください。" -ForegroundColor Green
            return
        }
    } catch {}

    if (!(Test-Path "package.json") -or !(Test-Path "server.ts")) {
        Write-Host ""
        Write-Host "⚡ tsbuild" -ForegroundColor Cyan -NoNewline; Write-Host "  v$localVersion" -ForegroundColor DarkGray
        Write-Host "Bun + TypeScript 開発サーバーをホットリロード付きで1コマンド起動するツール"
        Write-Host ""
        Write-Host "開発者  : " -NoNewline -ForegroundColor Yellow; Write-Host "Lapius7"
        Write-Host "X       : " -NoNewline -ForegroundColor Yellow; Write-Host "https://x.com/Lapius7"
        Write-Host "GitHub  : " -NoNewline -ForegroundColor Yellow; Write-Host "https://github.com/Lapius7/tsbuild"
        Write-Host ""
        if ($null -ne $remoteVersion) {
            if ($remoteVersion -eq $localVersion) {
                Write-Host "バージョン  : $localVersion  " -NoNewline; Write-Host "✅ 最新です" -ForegroundColor Green
            } else {
                Write-Host "バージョン  : $localVersion  " -NoNewline; Write-Host "⬆ 最新: $remoteVersion" -ForegroundColor Yellow
            }
        } else {
            Write-Host "バージョン  : $localVersion  " -NoNewline; Write-Host "(バージョン確認失敗)" -ForegroundColor DarkGray
        }
        Write-Host ""
        Write-Host "使い方  : tssetup でプロジェクトを作成してから、そのフォルダ内で tsbuild を実行してください" -ForegroundColor DarkGray
        Write-Host "ヘルプ  : tsbuild -Help" -ForegroundColor DarkGray
        Write-Host ""
        return
    }

    if ($Help) {
        Write-Host "`n⚡ [tsbuild] コマンドヘルプ" -ForegroundColor Cyan
        Write-Host "==================================================" -ForegroundColor DarkGray
        Write-Host "開発用サーバーの起動、および変更の自動ビルド（Watch）を一括実行します。"
        Write-Host "`n使い方:" -ForegroundColor Yellow
        Write-Host "  tsbuild"
        Write-Host "`n機能:" -ForegroundColor Yellow
        Write-Host "  1. バックグラウンドでBunによる高速Webサーバー起動（ポート自動競合回避）"
        Write-Host "  2. 初回コンパイル実行によるブラウザ読み込みエラー(404)の完全防止"
        Write-Host "  3. ブラウザの自動起動"
        Write-Host "  4. tsc --watch によるリアルタイム自動コンパイル"
        Write-Host "  5. ファイル変更時のブラウザ自動更新（ホットリロード）"
        Write-Host "  6. [Ctrl + C] 終了時のゾンビプロセス自動クリーンアップ"
        Write-Host "`n📁 対象プロジェクトの構成:" -ForegroundColor Yellow
        Write-Host "  myapp/"
        Write-Host "  ├── src/"
        Write-Host "  │   └── index.ts"
        Write-Host "  ├── dist/              " -NoNewline; Write-Host "← tsc が自動生成" -ForegroundColor DarkGray
        Write-Host "  ├── index.html"
        Write-Host "  ├── server.ts          " -NoNewline; Write-Host "← tsbuild が起動するサーバー" -ForegroundColor DarkGray
        Write-Host "  ├── tsconfig.json"
        Write-Host "  └── package.json"
        Write-Host "==================================================`n" -ForegroundColor DarkGray
        return
    }

    if (!(Test-Path "package.json") -or !(Test-Path "server.ts")) {
        Write-Error "エラー: package.json または server.ts がありません。プロジェクトのルートで実行してください。"
        return
    }

    Write-Host "🚀 開発環境を起動中（ホットリロード有効）..." -ForegroundColor Cyan

    $currentDir = (Get-Location).Path
    $serverJob = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        bun server.ts
    } -ArgumentList $currentDir

    $tscOutput = bun x tsc 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠ TypeScript コンパイルエラー:" -ForegroundColor Yellow
        $tscOutput | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    }

    $targetUrl = "http://localhost:53000"
    $maxWait = 5000
    $waited = 0
    while ($waited -lt $maxWait) {
        Start-Sleep -Milliseconds 200
        $waited += 200
        $combined = Receive-Job -Job $serverJob -Keep | Out-String
        if ($combined -match "http://localhost:\d+") {
            $targetUrl = $matches[0]
            break
        }
    }
    Start-Process $targetUrl

    Write-Host "==================================================" -ForegroundColor Yellow
    Write-Host " 🔥 ホットリロード稼働中！コードを変更するとブラウザが自動更新されます。" -ForegroundColor Green
    Write-Host " [Ctrl + C] を押すと、すべてのプロセスを終了します。" -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Yellow
    
    try {
        bun x tsc --watch
    }
    finally {
        Write-Host "`n🛑 開発環境を停止しています..." -ForegroundColor Red
        Get-Job | Where-Object { $_.State -eq "Running" } | Stop-Job
        Get-Job | Remove-Job
        Write-Host "✨ すべてのプロセスが正常に終了しました。" -ForegroundColor Green
    }
}
'@

if (!(Test-Path $PROFILE)) {
    New-Item -Type File -Path $PROFILE -Force > $null
}

$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ([string]::IsNullOrEmpty($profileContent)) { $profileContent = "" }

$beginMarker = "# <<BEGIN:$functionName>>"
$endMarker = "# <<END:$functionName>>"
$markerPattern = "(?s)# <<BEGIN:$functionName>>.*?# <<END:$functionName>>"

if ($profileContent -match $markerPattern) {
    $profileContent = $profileContent -replace $markerPattern, ""
} elseif ($profileContent -match "function\s+$functionName\b") {
    Write-Host ""
    Write-Host "⚠ 警告: マーカーのない旧バージョンの $functionName がプロファイルに存在します。" -ForegroundColor Yellow
    Write-Host "  自動削除は行いません。以下を手動で実行してください：" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. メモ帳でプロファイルを開く：" -ForegroundColor Cyan
    Write-Host "     notepad `$PROFILE" -ForegroundColor White
    Write-Host "  2. 'function $functionName' から始まるブロックを手動で削除する" -ForegroundColor Cyan
    Write-Host "  3. 保存後にこのインストールコマンドを再実行する" -ForegroundColor Cyan
    Write-Host ""
    return
}

$block = "$beginMarker`n$functionCode`n$endMarker"
$newProfileContent = $profileContent.Trim() + "`n`n" + $block
[System.IO.File]::WriteAllText($PROFILE, $newProfileContent.Trim(), [System.Text.UTF8Encoding]::new($true))

Invoke-Expression $functionCode

Write-Host "✨ tsbuild コマンドのインストール/更新が完了しました！" -ForegroundColor Green
Write-Host ""
Write-Host "📦 インストールコマンド（再インストール・更新時）:" -ForegroundColor Cyan
Write-Host "  irm https://raw.githubusercontent.com/Lapius7/tsbuild/main/install.ps1 | iex"
Write-Host ""
Write-Host "📋 使い方:" -ForegroundColor Cyan
Write-Host "  tsbuild          " -NoNewline; Write-Host "# 開発サーバー起動・ホットリロード開始" -ForegroundColor DarkGray
Write-Host "  tsbuild -Help    " -NoNewline; Write-Host "# 詳細ヘルプを表示" -ForegroundColor DarkGray
Write-Host ""
Write-Host "📁 対象プロジェクトの構成（tssetup で作成した場合）:" -ForegroundColor Cyan
Write-Host "  myapp/"
Write-Host "  ├── src/"
Write-Host "  │   └── index.ts"
Write-Host "  ├── dist/              " -NoNewline; Write-Host "← tsc が自動生成" -ForegroundColor DarkGray
Write-Host "  ├── index.html"
Write-Host "  ├── server.ts          " -NoNewline; Write-Host "← tsbuild が起動するサーバー" -ForegroundColor DarkGray
Write-Host "  ├── tsconfig.json"
Write-Host "  └── package.json"
Write-Host ""
Write-Host "🚀 プロジェクトの始め方:" -ForegroundColor Cyan
Write-Host "  tssetup myapp    " -NoNewline; Write-Host "# プロジェクト作成" -ForegroundColor DarkGray
Write-Host "  cd myapp         " -NoNewline; Write-Host "# ディレクトリ移動" -ForegroundColor DarkGray
Write-Host "  tsbuild          " -NoNewline; Write-Host "# 開発サーバー起動" -ForegroundColor DarkGray
Write-Host ""
Write-Host "新しいPowerShellウィンドウを開くか、 '. `$PROFILE' を実行して即時反映させてください。" -ForegroundColor Yellow
