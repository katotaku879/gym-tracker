# ui/main_window.py
import logging
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, 
                               QWidget, QMenuBar, QStatusBar, QMessageBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from database.db_manager import DatabaseManager
from utils.constants import (WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
                           WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, APP_NAME)
from .record_tab import RecordTab
from .history_tab import HistoryTab
# 他のタブは段階的に有効化
# from .stats_tab import StatsTab
# from .goals_tab import GoalsTab

class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # データベースマネージャー初期化
        try:
            self.db_manager = DatabaseManager()
        except Exception as e:
            self.logger.critical(f"Database manager initialization failed: {e}")
            QMessageBox.critical(self, "データベースエラー", 
                               f"データベースの初期化に失敗しました:\n{str(e)}")
            raise
        
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        
    def init_ui(self):
        """UI初期化"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # 中央ウィジェット設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        layout = QVBoxLayout(central_widget)
        
        # タブウィジェット作成
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # タブ追加
        self.setup_tabs()
        
    def setup_tabs(self):
        """タブ設定"""
        try:
            # 記録タブ
            self.record_tab = RecordTab(self.db_manager)
            self.tab_widget.addTab(self.record_tab, "記録")
            
            # 履歴タブ（実装済み）
            self.history_tab = HistoryTab(self.db_manager)
            self.tab_widget.addTab(self.history_tab, "履歴")
            
            # 統計タブ（仮実装）
            stats_placeholder = QWidget()
            stats_layout = QVBoxLayout(stats_placeholder)
            stats_layout.addWidget(QLabel("統計タブ - 実装中"))
            self.tab_widget.addTab(stats_placeholder, "統計")
            
            # 目標タブ（仮実装）
            goals_placeholder = QWidget()
            goals_layout = QVBoxLayout(goals_placeholder)
            goals_layout.addWidget(QLabel("目標タブ - 実装中"))
            self.tab_widget.addTab(goals_placeholder, "目標")
            
            # タブ変更時のイベント
            self.tab_widget.currentChanged.connect(self.on_tab_changed)
            
        except Exception as e:
            self.logger.error(f"Tab setup failed: {e}")
            QMessageBox.critical(self, "初期化エラー", 
                               f"タブの初期化に失敗しました:\n{str(e)}")
    
    def on_tab_changed(self, index):
        """タブ変更時の処理"""
        try:
            # 履歴タブに切り替わった時にデータを更新
            if index == 1 and hasattr(self, 'history_tab'):  # 履歴タブのインデックス
                self.history_tab.refresh_data()
                self.statusBar().showMessage("履歴データを更新しました", 2000)
        except Exception as e:
            self.logger.warning(f"Tab change event failed: {e}")
    
    def setup_menu(self):
        """メニューバー設定"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        # データ更新アクション
        refresh_action = QAction("データ更新", self)
        refresh_action.triggered.connect(self.refresh_all_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # バックアップアクション
        backup_action = QAction("バックアップ作成", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        # 終了アクション
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        
        about_action = QAction("アプリについて", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """ステータスバー設定"""
        self.statusBar().showMessage("準備完了")
    
    def refresh_all_data(self):
        """全データ更新"""
        try:
            if hasattr(self, 'history_tab'):
                self.history_tab.refresh_data()
            self.statusBar().showMessage("データを更新しました", 3000)
        except Exception as e:
            self.logger.error(f"Data refresh failed: {e}")
            QMessageBox.warning(self, "更新エラー", "データの更新に失敗しました")
    
    def create_backup(self):
        """バックアップ作成"""
        try:
            if self.db_manager.backup_database():
                QMessageBox.information(self, "バックアップ", "バックアップを作成しました")
                self.statusBar().showMessage("バックアップ作成完了", 3000)
            else:
                QMessageBox.warning(self, "バックアップ", "バックアップの作成に失敗しました")
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            QMessageBox.critical(self, "バックアップエラー", 
                               f"バックアップ作成中にエラーが発生しました:\n{str(e)}")
    
    def show_about(self):
        """アプリについて表示"""
        QMessageBox.about(self, "GymTrackerについて", 
                         f"{APP_NAME}\n\n"
                         "個人向け筋トレ記録・成長追跡アプリケーション\n"
                         "PySide6 + SQLite + matplotlib")
    
    def closeEvent(self, event):
        """アプリケーション終了時の処理"""
        reply = QMessageBox.question(self, "終了確認", 
                                   "アプリケーションを終了しますか？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Application closing")
            event.accept()
        else:
            event.ignore()