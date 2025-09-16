@echo off
title GymTracker - 筋トレ記録アプリ
color 0A

echo ========================================
echo    🏋️ GymTracker 起動中...
echo ========================================
echo.

REM 作業ディレクトリに移動
cd /d "C:\Users\mkykr\Pythonプログラム\筋トレ記録アプリ"

REM Pythonの存在確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Pythonがインストールされていません
    echo    https://python.org からダウンロードしてください
    pause
    exit /b 1
)

REM 依存関係確認（初回のみ）
echo 📦 依存関係を確認中...
pip show PySide6 >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 必要なライブラリをインストールします...
    pip install -r requirements.txt
)

REM アプリケーション起動
echo 🚀 GymTrackerを起動します...
echo.
python main.py

REM エラー処理
if %errorlevel% neq 0 (
    echo.
    echo ❌ アプリケーションでエラーが発生しました
    echo 📋 ログファイル: logs/ フォルダを確認してください
    echo.
    pause
) else (
    echo.
    echo ✅ GymTrackerが正常に終了しました
    timeout /t 3 >nul
)

exit /b 0