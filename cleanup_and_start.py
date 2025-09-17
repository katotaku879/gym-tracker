#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡単プロセス終了・ファイルクリーンアップスクリプト
cleanup_and_start.py として保存
"""

import os
import glob
import subprocess
import sys
import time

def kill_python_processes():
    """Pythonプロセスを強制終了"""
    print("🔧 Pythonプロセス終了中...")
    
    try:
        # Windows用
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, check=False)
        subprocess.run(['taskkill', '/F', '/IM', 'pythonw.exe'], 
                      capture_output=True, check=False)
        print("✅ Pythonプロセス終了完了")
        time.sleep(1)  # 少し待機
    except Exception as e:
        print(f"⚠️ プロセス終了で問題: {e}")

def cleanup_test_files():
    """テストファイルをクリーンアップ"""
    print("🧹 テストファイルクリーンアップ中...")
    
    # 削除対象パターン
    patterns = [
        'test_*.db',
        'test_*.db-wal',
        'test_*.db-shm',
        '*.db-journal'
    ]
    
    deleted_files = []
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                deleted_files.append(file)
                print(f"   ✅ 削除: {file}")
            except PermissionError:
                print(f"   ❌ ロック中: {file}")
            except Exception as e:
                print(f"   ⚠️ エラー: {file} - {e}")
    
    if not deleted_files:
        print("   ✅ 削除対象ファイルなし")
    
    return len(deleted_files)

def check_main_db():
    """メインデータベースの状態確認"""
    print("📊 メインデータベース確認中...")
    
    main_db = 'gym_tracker.db'
    
    if os.path.exists(main_db):
        size = os.path.getsize(main_db)
        print(f"   ✅ {main_db} 存在 ({size:,} bytes)")
        
        # 書き込み可能かテスト
        try:
            with open(main_db, 'r+b') as f:
                pass
            print("   ✅ アクセス可能")
            return True
        except PermissionError:
            print("   ❌ ファイルロック中")
            return False
    else:
        print("   ✅ メインDB未作成（初回起動時に作成されます）")
        return True

def start_app():
    """アプリケーション起動"""
    print("🚀 GymTracker 起動中...")
    
    try:
        # 環境チェック
        print("   PySide6チェック中...")
        import PySide6
        print("   ✅ PySide6 OK")
        
        print("   UIモジュールチェック中...")
        from ui.main_window import MainWindow
        print("   ✅ UIモジュール OK")
        
        # アプリ起動
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("GymTracker")
        
        window = MainWindow()
        window.show()
        
        print("✅ 起動成功！新しい「🎯 体組成目標」タブを確認してください")
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("必要なライブラリをインストール:")
        print("pip install PySide6 matplotlib")
        return False
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    print("🔧 GymTracker クリーンアップ & 起動")
    print("=" * 50)
    
    # 1. プロセス終了
    kill_python_processes()
    
    # 2. ファイルクリーンアップ
    deleted_count = cleanup_test_files()
    
    # 3. メインDB確認
    db_ok = check_main_db()
    
    # 4. 結果表示
    print("\n📋 クリーンアップ結果:")
    print(f"   削除ファイル数: {deleted_count}")
    print(f"   メインDB状態: {'正常' if db_ok else '問題あり'}")
    
    if not db_ok:
        print("\n⚠️ メインデータベースに問題があります")
        print("PCを再起動してから再実行してください")
        input("Enterキーで終了...")
        return
    
    # 5. アプリ起動
    print("\n" + "=" * 50)
    start_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作が中断されました")
    except Exception as e:
        print(f"\nエラー: {e}")
        input("Enterキーで終了...")