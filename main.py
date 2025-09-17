# main.py - 起動問題修正版

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 最小限のimportで開始
print("Starting GymTracker...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

def setup_logging_minimal():
    """最小限のログ設定"""
    try:
        # logsディレクトリ作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # ログファイル設定
        log_file = log_dir / f"gym_tracker_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Minimal logging setup completed")
        return True
        
    except Exception as e:
        print(f"Logging setup failed: {e}")
        return False

def check_python_version():
    """Python バージョンチェック"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8以上が必要です")
        print(f"現在のバージョン: {sys.version}")
        return False
    
    print(f"✅ Python バージョンOK: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_critical_imports():
    """重要なライブラリのインポートチェック"""
    critical_libs = {
        'PySide6': 'pip install PySide6',
        'sqlite3': '標準ライブラリ（通常問題なし）'
    }
    
    missing_libs = []
    
    for lib, install_cmd in critical_libs.items():
        try:
            if lib == 'PySide6':
                import PySide6
                from PySide6.QtWidgets import QApplication, QMessageBox
                print(f"✅ {lib} インポートOK")
            elif lib == 'sqlite3':
                import sqlite3
                print(f"✅ {lib} インポートOK")
        except ImportError as e:
            print(f"❌ {lib} インポート失敗: {e}")
            print(f"   インストール方法: {install_cmd}")
            missing_libs.append(lib)
    
    return len(missing_libs) == 0, missing_libs

def check_file_structure():
    """ファイル構造チェック"""
    required_files = [
        'main.py',
        'database/__init__.py',
        'database/db_manager.py',
        'database/models.py',
        'ui/__init__.py',
        'ui/main_window.py',
        'ui/base_tab.py',
        'utils/__init__.py',
        'utils/constants.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 必要ファイル不在: {file_path}")
            missing_files.append(file_path)
        else:
            print(f"✅ ファイル存在: {file_path}")
    
    return len(missing_files) == 0, missing_files

def safe_import_database():
    """データベースモジュールの安全なインポート"""
    try:
        sys.path.append(os.getcwd())
        
        print("データベースモジュールをインポート中...")
        from database.db_manager import DatabaseManager
        from database.models import Exercise, Workout, Set, Goal
        print("✅ データベースモジュール インポートOK")
        return True
    except Exception as e:
        print(f"❌ データベースモジュール インポート失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def safe_import_ui():
    """UIモジュールの安全なインポート"""
    try:
        print("UIモジュールをインポート中...")
        from ui.main_window import MainWindow
        print("✅ UIモジュール インポートOK")
        return True
    except Exception as e:
        print(f"❌ UIモジュール インポート失敗: {e}")
        import traceback
        traceback.print_exc()
        return False



def safe_main():
    """安全なメイン関数"""
    print("=" * 50)
    print("🏋️ GymTracker 起動診断")
    print("=" * 50)
    
    # 1. ログ設定
    if not setup_logging_minimal():
        print("❌ ログ設定失敗")
        return False
    
    logger = logging.getLogger(__name__)
    
    # 2. Python バージョンチェック
    if not check_python_version():
        return False
    
    # 3. ファイル構造チェック
    files_ok, missing_files = check_file_structure()
    if not files_ok:
        print(f"❌ 必要ファイルが不足しています: {missing_files}")
        return False
    
    # 4. 重要ライブラリチェック
    libs_ok, missing_libs = check_critical_imports()
    if not libs_ok:
        print(f"❌ 必要ライブラリが不足しています: {missing_libs}")
        print("\n📦 インストール方法:")
        print("pip install PySide6 matplotlib")
        return False
    
    # 5. データベースモジュールテスト
    if not safe_import_database():
        return False
    
    
    # 7. UIモジュールテスト
    if not safe_import_ui():
        return False
    
    # 8. アプリケーション起動
    try:
        print("アプリケーション起動中...")
        
        from PySide6.QtWidgets import QApplication, QMessageBox
        from ui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("GymTracker")
        app.setApplicationVersion("1.0 (診断版)")
        
        print("メインウィンドウ作成中...")
        window = MainWindow()
        
        print("ウィンドウ表示中...")
        window.show()
        
        logger.info("✅ アプリケーション起動成功！")
        print("✅ アプリケーション起動成功！")
        
        # イベントループ開始
        result = app.exec()
        logger.info(f"アプリケーション終了: コード {result}")
        return True
        
    except Exception as e:
        logger.error(f"❌ アプリケーション起動失敗: {e}")
        print(f"❌ アプリケーション起動失敗: {e}")
        import traceback
        traceback.print_exc()
        
        # エラーダイアログ表示（可能であれば）
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if not QApplication.instance():
                app = QApplication(sys.argv)
            
            QMessageBox.critical(None, "起動エラー", 
                               f"アプリケーションの起動に失敗しました:\n\n{str(e)}\n\n"
                               "ログファイル（logs/フォルダ）を確認してください。")
        except:
            pass
        
        return False

# 診断機能付きmain関数
def main():
    """メイン関数（診断機能付き）"""
    try:
        success = safe_main()
        if not success:
            print("\n" + "=" * 50)
            print("❌ 起動に失敗しました")
            print("=" * 50)
            print("\n🔧 トラブルシューティング:")
            print("1. 必要なライブラリをインストール:")
            print("   pip install PySide6 matplotlib")
            print("2. ファイル構造を確認")
            print("3. Python 3.8以上を使用")
            print("4. ログファイル（logs/フォルダ）を確認")
            print("5. 管理者権限で実行")
            
            input("\n続行するには何かキーを押してください...")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ ユーザーによってアプリケーションが中断されました")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        input("\n続行するには何かキーを押してください...")
        sys.exit(1)

if __name__ == "__main__":
    main()