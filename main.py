# main.py の改良版
import sys
import os
import logging
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from ui.main_window import MainWindow

class CriticalErrorHandler:
    """致命的エラーハンドラー"""
    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """未処理例外ハンドラー"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.critical(f"Uncaught exception: {error_msg}")
        
        # ユーザーにエラーを通知
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("致命的エラー")
            msg_box.setText("予期しないエラーが発生しました。\nアプリケーションを終了します。")
            msg_box.setDetailedText(error_msg)
            msg_box.exec()
        except:
            pass  # GUI が利用できない場合は何もしない

def setup_logging():
    """ログ設定（改良版）"""
    try:
        # ログディレクトリ作成
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # ログファイル名（日付付き）
        from datetime import datetime
        log_file = os.path.join(log_dir, f"gym_tracker_{datetime.now().strftime('%Y%m%d')}.log")
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # アプリケーション開始ログ
        logging.info("=" * 50)
        logging.info("GymTracker Application Starting")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Working directory: {os.getcwd()}")
        logging.info("=" * 50)
        return True
    except Exception as e:
        print(f"Logging setup failed: {e}")
        return False

def check_dependencies():
    """依存関係チェック"""
    try:
        import PySide6
        import matplotlib
        import sqlite3
        logging.info("All dependencies are available")
        return True
    except ImportError as e:
        error_msg = f"必要なライブラリが見つかりません: {e}"
        logging.error(error_msg)
        QMessageBox.critical(None, "依存関係エラー",
            f"{error_msg}\n\n以下のコマンドで必要なライブラリをインストールしてください:\n"
            "pip install PySide6 matplotlib")
        return False

def check_file_permissions():
    """ファイル権限チェック"""
    try:
        # 書き込み権限テスト
        test_file = "permission_test.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        logging.info("File permissions OK")
        return True
    except PermissionError:
        error_msg = "ファイルの読み書き権限がありません"
        logging.error(error_msg)
        QMessageBox.critical(None, "権限エラー",
            f"{error_msg}\n\n管理者権限で実行するか、実行可能なディレクトリに移動してください。")
        return False
    except Exception as e:
        logging.warning(f"Permission check failed: {e}")
        return True  # 権限チェック失敗は致命的ではない

def main():
    """メイン関数（改良版）"""
    # 未処理例外ハンドラー設定
    sys.excepthook = CriticalErrorHandler.handle_exception
    
    # ログ設定
    if not setup_logging():
        sys.exit(1)
    
    logger = logging.getLogger(__name__)
    
    try:
        # アプリケーション作成
        app = QApplication(sys.argv)
        app.setApplicationName("GymTracker")
        app.setApplicationVersion("1.0")
        
        # 依存関係チェック
        if not check_dependencies():
            sys.exit(1)
        
        # ファイル権限チェック
        if not check_file_permissions():
            sys.exit(1)
        
        # メインウィンドウ作成
        try:
            window = MainWindow()
        except Exception as e:
            logger.critical(f"MainWindow creation failed: {e}")
            QMessageBox.critical(None, "初期化エラー",
                f"アプリケーションの初期化に失敗しました:\n{str(e)}")
            sys.exit(1)
        
        # ウィンドウ表示
        window.show()
        logger.info("Application window displayed")
        
        # 初期化後のメモリチェック（エラー回避）
        try:
            from utils.memory_manager import MemoryManager
            QTimer.singleShot(1000, lambda: MemoryManager.check_memory_limit())
        except Exception as e:
            logger.warning(f"Memory manager initialization failed: {e}")
        
        # アプリケーション実行
        result = app.exec()
        logger.info(f"Application exited with code: {result}")
        sys.exit(result)
        
    except Exception as e:
        logger.critical(f"Application startup failed: {e}")
        try:
            QMessageBox.critical(None, "起動エラー",
                f"アプリケーションの起動に失敗しました:\n{str(e)}")
        except:
            print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()