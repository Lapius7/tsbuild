# 💡 インストールを実行するPowerShellスクリプト
$functionName = "tsbuild"
$functionCode = @'
function tsbuild {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)][switch]$Help
    )

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
$oldPattern = "(?s)function\s+$functionName\s*\{.*?\r?\n\}"

if ($profileContent -match $markerPattern) {
    $profileContent = $profileContent -replace $markerPattern, ""
} elseif ($profileContent -match $oldPattern) {
    $profileContent = $profileContent -replace $oldPattern, ""
}

$block = "$beginMarker`n$functionCode`n$endMarker"
$newProfileContent = $profileContent.Trim() + "`n`n" + $block
$newProfileContent.Trim() | Out-File -FilePath $PROFILE -Encoding utf8 -Force

Invoke-Expression $functionCode

Write-Host "✨ tsbuild コマンドのインストール/更新が完了しました！" -ForegroundColor Green
Write-Host ""
Write-Host "📦 インストールコマンド（再インストール・更新時）:" -ForegroundColor Cyan
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`""
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
