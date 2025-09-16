# ui/main_window.py - 完全修正版（Pylanceエラー完全解消）
import logging
from typing import Optional, Union, Any, Protocol
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, 
                               QWidget, QMenuBar, QStatusBar, QMessageBox, 
                               QLabel, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont

from database.db_manager import DatabaseManager
from utils.constants import (WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
                           WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, APP_NAME)
from .record_tab import RecordTab
from .history_tab import HistoryTab

# 統計タブをインポート
try:
    from .stats_tab import StatsTab
    STATS_TAB_AVAILABLE = True
except ImportError as e:
    STATS_TAB_AVAILABLE = False
    print(f"Stats tab import failed: {e}")

# 目標タブをインポート
try:
    from .goals_tab import GoalsTab
    GOALS_TAB_AVAILABLE = True
except ImportError as e:
    GOALS_TAB_AVAILABLE = False
    print(f"Goals tab import failed: {e}")

# 型定義用のプロトコル
class RefreshableTab(Protocol):
    """refresh_dataメソッドを持つタブのプロトコル"""
    def refresh_data(self) -> None:
        ...

class LoadableTab(Protocol):
    """load_exercisesメソッドを持つタブのプロトコル"""
    def load_exercises(self) -> None:
        ...

class MainWindow(QMainWindow):
    """メインウィンドウ - 完全修正版"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # タブの型注釈
        self.record_tab: Optional[RecordTab] = None
        self.history_tab: Optional[HistoryTab] = None
        self.stats_tab: Optional[Union['StatsTab', QWidget]] = None
        self.goals_tab: Optional[Union['GoalsTab', QWidget]] = None
        self.settings_tab: Optional[QWidget] = None
        
        # データベースマネージャー初期化
        try:
            self.db_manager = DatabaseManager()
            self.logger.info("Database manager initialized successfully")
        except Exception as e:
            self.logger.critical(f"Database manager initialization failed: {e}")
            QMessageBox.critical(self, "データベースエラー", 
                               f"データベースの初期化に失敗しました:\n{str(e)}")
            raise
        
        self.init_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # 起動メッセージ
        self.statusBar().showMessage("GymTracker へようこそ！ 💪", 3000)
        
    def init_ui(self):
        """UI初期化"""
        self.setWindowTitle(f"{APP_NAME} - 筋トレ記録・成長追跡アプリ")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        
        # 中央ウィジェット設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # タイトル
        title_label = QLabel("🏋️ GymTracker - 筋トレ記録・成長追跡")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # タブウィジェット作成
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #bdc3c7;
            }
        """)
        layout.addWidget(self.tab_widget)
        
        # タブ追加
        self.setup_tabs()
    
    def has_refresh_data(self, obj: Any) -> bool:
        """オブジェクトがrefresh_dataメソッドを持っているかチェック"""
        return hasattr(obj, 'refresh_data') and callable(getattr(obj, 'refresh_data'))

    def has_load_exercises(self, obj: Any) -> bool:
        """オブジェクトがload_exercisesメソッドを持っているかチェック"""
        return hasattr(obj, 'load_exercises') and callable(getattr(obj, 'load_exercises'))

    def call_refresh_data(self, obj: Any) -> bool:
        """型安全なrefresh_data呼び出し"""
        try:
            if self.has_refresh_data(obj):
                obj.refresh_data()
                return True
            return False
        except Exception as e:
            self.logger.error(f"refresh_data call failed: {e}")
            return False

    def call_load_exercises(self, obj: Any) -> bool:
        """型安全なload_exercises呼び出し"""
        try:
            if self.has_load_exercises(obj):
                obj.load_exercises()
                return True
            return False
        except Exception as e:
            self.logger.error(f"load_exercises call failed: {e}")
            return False
        
    def setup_tabs(self):
        """タブ設定 - 完全修正版"""
        try:
            # 記録タブ
            self.logger.info("Setting up Record tab...")
            self.record_tab = RecordTab(self.db_manager)
            self.tab_widget.addTab(self.record_tab, "📝 記録")
            
            # 履歴タブ
            self.logger.info("Setting up History tab...")
            self.history_tab = HistoryTab(self.db_manager)
            self.tab_widget.addTab(self.history_tab, "📚 履歴")
            
            # 統計タブ（条件付き）
            if STATS_TAB_AVAILABLE:
                try:
                    self.logger.info("Setting up Stats tab...")
                    self.stats_tab = StatsTab(self.db_manager)
                    self.tab_widget.addTab(self.stats_tab, "📊 統計")
                    self.logger.info("Stats tab loaded successfully")
                except Exception as e:
                    self.logger.error(f"Stats tab creation failed: {e}")
                    self.stats_tab = self.create_stats_placeholder()
                    self.tab_widget.addTab(self.stats_tab, "📊 統計（エラー）")
                    QMessageBox.warning(self, "統計タブエラー", 
                                      f"統計タブの作成に失敗しました:\n{str(e)}\n\n"
                                      "プレースホルダーが表示されます。")
            else:
                # フォールバック：統計プレースホルダー
                self.stats_tab = self.create_stats_placeholder()
                self.tab_widget.addTab(self.stats_tab, "📊 統計（要インストール）")
                self.logger.warning("Stats tab not available - using placeholder")
            
            # 目標タブ（完全実装版）
            if GOALS_TAB_AVAILABLE:
                try:
                    self.logger.info("Setting up Goals tab...")
                    self.goals_tab = GoalsTab(self.db_manager)
                    self.tab_widget.addTab(self.goals_tab, "🎯 目標")
                    self.logger.info("Goals tab loaded successfully")
                except Exception as e:
                    self.logger.error(f"Goals tab creation failed: {e}")
                    # フォールバック：プレースホルダー
                    self.goals_tab = self.create_goals_placeholder()
                    self.tab_widget.addTab(self.goals_tab, "🎯 目標（エラー）")
                    QMessageBox.warning(self, "目標タブエラー", 
                                      f"目標タブの作成に失敗しました:\n{str(e)}\n\n"
                                      "プレースホルダーが表示されます。")
            else:
                # フォールバック：プレースホルダー
                self.goals_tab = self.create_goals_placeholder()
                self.tab_widget.addTab(self.goals_tab, "🎯 目標（実装中）")
                self.logger.warning("Goals tab not available - using placeholder")
            
            # 設定タブ（プレースホルダー）
            self.settings_tab = self.create_settings_placeholder()
            self.tab_widget.addTab(self.settings_tab, "⚙️ 設定")
            
            # タブ変更時のイベント
            self.tab_widget.currentChanged.connect(self.on_tab_changed)
            
            self.logger.info("All tabs setup completed")
            
        except Exception as e:
            self.logger.error(f"Tab setup failed: {e}")
            QMessageBox.critical(self, "初期化エラー", 
                               f"タブの初期化に失敗しました:\n{str(e)}")
    
    def create_stats_placeholder(self) -> QWidget:
        """統計タブプレースホルダー作成"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        
        # タイトル
        title = QLabel("📊 統計・分析機能")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #e74c3c; margin: 20px;")
        layout.addWidget(title)
        
        # メッセージ
        if not STATS_TAB_AVAILABLE:
            message = QLabel("""
統計機能を使用するには以下のライブラリが必要です：

📦 必要なライブラリ：
• matplotlib（グラフ描画）
• pandas（データ処理）

💻 インストール方法：
pip install matplotlib pandas

🔄 インストール後、アプリケーションを再起動してください。

📈 利用可能になる機能：
• 1RM推移グラフ
• 重量・ボリューム推移
• 頻度分析（曜日別・部位別）
• ベスト記録一覧
• 成長統計
            """)
        else:
            message = QLabel("""
❌ 統計タブの初期化に失敗しました

🔧 トラブルシューティング：
• アプリケーションを再起動してください
• ログファイルで詳細を確認してください
• 必要に応じてライブラリを再インストールしてください

pip install --upgrade matplotlib pandas
            """)
        
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 2px dashed #bdc3c7;
                margin: 20px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(message)
        
        # リトライボタン（統計タブが利用できない場合のみ）
        if not STATS_TAB_AVAILABLE:
            retry_btn = QPushButton("🔄 再試行")
            retry_btn.clicked.connect(self.retry_stats_tab)
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """)
            layout.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        
        return placeholder
    
    def create_goals_placeholder(self) -> QWidget:
        """目標タブプレースホルダー作成"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        
        title = QLabel("🎯 目標管理機能")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #f39c12; margin: 20px;")
        layout.addWidget(title)
        
        if not GOALS_TAB_AVAILABLE:
            message = QLabel("""
目標管理機能の読み込みに失敗しました 🚧

📋 予定されている機能：
• 月間目標設定
• 進捗追跡
• 達成率表示
• 目標達成通知
• 目標履歴管理

🔧 トラブルシューティング：
• goals_tab.py ファイルが存在するか確認
• アプリケーションを再起動
• エラーログを確認

🔜 実装完了後に利用可能になります！
            """)
        else:
            message = QLabel("""
目標管理機能は開発中です 🚧

📋 予定されている機能：
• 月間目標設定
• 進捗追跡
• 達成率表示
• 目標達成通知
• 目標履歴管理

🔜 近日公開予定です！
            """)
        
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background-color: #fff3cd;
                padding: 20px;
                border-radius: 8px;
                border: 2px dashed #f39c12;
                margin: 20px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(message)
        layout.addStretch()
        
        return placeholder
    
    def create_settings_placeholder(self) -> QWidget:
        """設定タブプレースホルダー作成"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        
        title = QLabel("⚙️ 設定機能")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #95a5a6; margin: 20px;")
        layout.addWidget(title)
        
        message = QLabel("""
設定機能は開発中です 🚧

🔧 予定されている機能：
• データベース管理
• バックアップ・復元
• データエクスポート
• テーマ設定
• 通知設定

🔜 近日公開予定です！
        """)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background-color: #f4f4f4;
                padding: 20px;
                border-radius: 8px;
                border: 2px dashed #95a5a6;
                margin: 20px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(message)
        layout.addStretch()
        
        return placeholder
    
    def retry_stats_tab(self):
        """統計タブの再試行"""
        try:
            # モジュールの再インポートを試行
            import importlib
            import sys
            
            # stats_tabモジュールがすでにインポートされている場合はリロード
            if 'ui.stats_tab' in sys.modules:
                importlib.reload(sys.modules['ui.stats_tab'])
            
            from .stats_tab import StatsTab
            
            # 既存のタブを削除
            for i in range(self.tab_widget.count()):
                if "統計" in self.tab_widget.tabText(i):
                    self.tab_widget.removeTab(i)
                    break
            
            # 新しい統計タブを作成
            self.stats_tab = StatsTab(self.db_manager)
            self.tab_widget.insertTab(2, self.stats_tab, "📊 統計")
            
            QMessageBox.information(self, "成功", "📊 統計タブが正常に読み込まれました！")
            self.statusBar().showMessage("統計タブが利用可能になりました", 3000)
            
        except Exception as e:
            self.logger.error(f"Stats tab retry failed: {e}")
            QMessageBox.warning(self, "再試行失敗", 
                              f"統計タブの読み込みに失敗しました:\n{str(e)}\n\n"
                              "必要なライブラリがインストールされているか確認してください。")
    
    def on_tab_changed(self, index: int):
        """タブ変更時の処理 - 完全修正版"""
        try:
            tab_name = self.tab_widget.tabText(index)
            current_tab = self.tab_widget.widget(index)
            self.logger.info(f"Tab changed to: {tab_name}")
            
            # 履歴タブに切り替わった時にデータを更新
            if "履歴" in tab_name and current_tab is self.history_tab:
                if self.history_tab and self.has_refresh_data(self.history_tab):
                    try:
                        self.history_tab.refresh_data()
                        self.statusBar().showMessage("履歴データを更新しました", 2000)
                    except Exception as e:
                        self.logger.warning(f"History tab refresh failed: {e}")
            
            # 統計タブに切り替わった時にデータを更新
            elif "統計" in tab_name and current_tab is self.stats_tab:
                if self.stats_tab and self.has_refresh_data(self.stats_tab):
                    try:
                        self.call_refresh_data(self.stats_tab)
                        self.statusBar().showMessage("統計データを更新しました", 2000)
                    except Exception as e:
                        self.logger.warning(f"Stats tab refresh failed: {e}")
            
            # 目標タブに切り替わった時にデータを更新
            elif "目標" in tab_name and current_tab is self.goals_tab:
                if self.goals_tab and self.has_refresh_data(self.goals_tab):
                    try:
                        self.call_refresh_data(self.goals_tab)
                        
                        # 目標の進捗を最新のトレーニング記録から自動更新
                        if hasattr(self.db_manager, 'update_goal_progress_from_recent_records'):
                            updated_count = self.db_manager.update_goal_progress_from_recent_records()
                            if updated_count > 0:
                                self.statusBar().showMessage(f"目標データを更新しました（進捗更新: {updated_count}件）", 3000)
                            else:
                                self.statusBar().showMessage("目標データを更新しました", 2000)
                        else:
                            self.statusBar().showMessage("目標データを更新しました", 2000)
                    except Exception as e:
                        self.logger.warning(f"Goals tab refresh failed: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Tab change event failed: {e}")
        
    def setup_menu(self):
        """メニューバー設定"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("📁 ファイル")
        
        # データ更新アクション
        refresh_action = QAction("🔄 データ更新", self)
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.triggered.connect(self.refresh_all_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        # バックアップアクション
        backup_action = QAction("💾 バックアップ作成", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        # データエクスポートアクション
        export_action = QAction("📤 データエクスポート", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 終了アクション
        exit_action = QAction("🚪 終了", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu("👁️ 表示")
        
        # フルスクリーンアクション
        fullscreen_action = QAction("🖥️ フルスクリーン", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # ツールメニュー
        tools_menu = menubar.addMenu("🔧 ツール")
        
        # データベース整合性チェック
        check_db_action = QAction("🔍 データベースチェック", self)
        check_db_action.triggered.connect(self.check_database_integrity)
        tools_menu.addAction(check_db_action)
        
        # ログ表示
        show_logs_action = QAction("📋 ログ表示", self)
        show_logs_action.triggered.connect(self.show_logs)
        tools_menu.addAction(show_logs_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("❓ ヘルプ")
        
        # 使い方ガイド
        guide_action = QAction("📖 使い方ガイド", self)
        guide_action.triggered.connect(self.show_guide)
        help_menu.addAction(guide_action)
        
        help_menu.addSeparator()
        
        # アプリについて
        about_action = QAction("ℹ️ アプリについて", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """ステータスバー設定"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #34495e;
                color: white;
                font-weight: bold;
            }
        """)
        status_bar.showMessage("準備完了 💪")
    
    def refresh_all_data(self):
        """全データ更新 - 完全修正版"""
        try:
            self.statusBar().showMessage("データを更新中...", 1000)
            
            # 各タブのデータを更新（型安全な呼び出し）
            refresh_count = 0
            
            if self.call_refresh_data(self.history_tab):
                refresh_count += 1
            
            if self.call_refresh_data(self.stats_tab):
                refresh_count += 1
            
            # 記録タブには複数の可能性があるメソッド名
            if not self.call_refresh_data(self.record_tab):
                if self.call_load_exercises(self.record_tab):
                    refresh_count += 1
            else:
                refresh_count += 1
            
            # 目標タブのデータ更新
            if self.call_refresh_data(self.goals_tab):
                refresh_count += 1
                
                # 目標進捗の自動更新
                try:
                    if hasattr(self.db_manager, 'update_goal_progress_from_recent_records'):
                        updated_goals = self.db_manager.update_goal_progress_from_recent_records()
                        if updated_goals > 0:
                            self.logger.info(f"Auto-updated {updated_goals} goals from recent records")
                except Exception as e:
                    self.logger.warning(f"Goal progress auto-update failed: {e}")
            
            self.statusBar().showMessage(f"✅ {refresh_count}個のタブのデータを更新しました", 3000)
            QMessageBox.information(self, "更新完了", f"📊 {refresh_count}個のタブを更新しました！")
            
        except Exception as e:
            self.logger.error(f"Data refresh failed: {e}")
            QMessageBox.warning(self, "更新エラー", f"データの更新に失敗しました:\n{str(e)}")
    
    def create_backup(self):
        """バックアップ作成"""
        try:
            self.statusBar().showMessage("バックアップを作成中...", 2000)
            
            if hasattr(self.db_manager, 'backup_database'):
                if self.db_manager.backup_database():
                    QMessageBox.information(self, "バックアップ完了", 
                                          "💾 バックアップを正常に作成しました！\n\n"
                                          "バックアップファイルは backup/ フォルダに保存されています。")
                    self.statusBar().showMessage("✅ バックアップ作成完了", 3000)
                else:
                    QMessageBox.warning(self, "バックアップエラー", "❌ バックアップの作成に失敗しました")
            else:
                QMessageBox.warning(self, "機能未実装", "🚧 バックアップ機能は実装中です")
                
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            QMessageBox.critical(self, "バックアップエラー", 
                               f"❌ バックアップ作成中にエラーが発生しました:\n{str(e)}")
    
    def export_data(self):
        """データエクスポート"""
        try:
            QMessageBox.information(self, "エクスポート", 
                                  "📤 データエクスポート機能は実装中です\n\n"
                                  "将来のバージョンで以下の形式をサポート予定：\n"
                                  "• CSV形式\n"
                                  "• Excel形式\n"
                                  "• JSON形式")
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
    
    def toggle_fullscreen(self):
        """フルスクリーン切り替え"""
        if self.isFullScreen():
            self.showNormal()
            self.statusBar().showMessage("通常表示に戻しました", 2000)
        else:
            self.showFullScreen()
            self.statusBar().showMessage("フルスクリーン表示（F11で戻る）", 3000)
    
    def check_database_integrity(self):
        """データベース整合性チェック"""
        try:
            self.statusBar().showMessage("データベースをチェック中...", 2000)
            
            # 基本的な整合性チェック
            with self.db_manager.get_connection() as conn:
                # テーブル存在チェック
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['exercises', 'workouts', 'sets', 'goals']
                missing_tables = set(expected_tables) - set(tables)
                
                if missing_tables:
                    QMessageBox.warning(self, "データベース警告", 
                                      f"⚠️ 以下のテーブルが見つかりません:\n{', '.join(missing_tables)}")
                else:
                    # レコード数チェック
                    cursor = conn.execute("SELECT COUNT(*) FROM exercises")
                    exercise_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM workouts")
                    workout_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM sets")
                    set_count = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM goals")
                    goal_count = cursor.fetchone()[0]
                    
                    QMessageBox.information(self, "データベースチェック完了", 
                                          f"✅ データベースは正常です\n\n"
                                          f"📊 データ統計:\n"
                                          f"• 種目数: {exercise_count}\n"
                                          f"• ワークアウト数: {workout_count}\n"
                                          f"• セット数: {set_count}\n"
                                          f"• 目標数: {goal_count}")
                    
            self.statusBar().showMessage("✅ データベースチェック完了", 3000)
            
        except Exception as e:
            self.logger.error(f"Database check failed: {e}")
            QMessageBox.critical(self, "チェックエラー", 
                               f"❌ データベースチェック中にエラーが発生しました:\n{str(e)}")
    
    def show_logs(self):
        """ログ表示"""
        try:
            QMessageBox.information(self, "ログ表示", 
                                  "📋 ログ表示機能は実装中です\n\n"
                                  "現在のログファイル場所:\n"
                                  "logs/ フォルダ内の日付別ファイル\n\n"
                                  "ログはテキストエディタで確認できます。")
        except Exception as e:
            self.logger.error(f"Show logs failed: {e}")
    
    def show_guide(self):
        """使い方ガイド表示"""
        guide_text = """
🏋️ GymTracker 使い方ガイド

📝 【記録タブ】
1. 日付を選択
2. 種目を選択  
3. 重量と回数を入力
4. 「セット追加」で複数セット記録
5. 「保存」でデータ保存

📚 【履歴タブ】
• 過去のトレーニング記録を確認
• 日付・種目でフィルタリング可能
• 記録の編集・削除も可能

📊 【統計タブ】
• 成長グラフの表示
• ベスト記録の確認
• 部位別分析
• 頻度分析

🎯 【目標タブ】
• 月間目標の設定
• 進捗追跡
• 達成率表示

⚙️ 【設定タブ】（開発中）
• データ管理
• バックアップ・復元

💡 ヒント：
• Ctrl+R でデータ更新
• F11 でフルスクリーン
• 定期的にバックアップを作成しましょう
        """
        
        QMessageBox.information(self, "📖 使い方ガイド", guide_text)
    
    def show_about(self):
        """アプリについて表示"""
        about_text = f"""
🏋️ {APP_NAME}

個人向け筋トレ記録・成長追跡デスクトップアプリケーション

📋 実装済み機能：
• トレーニング記録管理 ✅
• 履歴表示・フィルタリング ✅  
• 成長推移の可視化 ✅
• ベスト記録追跡 ✅
• 統計・分析機能 ✅
• 目標管理・進捗追跡 ✅

🛠️ 技術仕様：
• フロントエンド: PySide6 (Qt)
• データベース: SQLite
• グラフ描画: matplotlib
• データ処理: pandas

👨‍💻 開発：
オープンソースプロジェクト

📅 バージョン：
1.0.0 - 2024年版

💪 健康的なトレーニングライフを応援します！
        """
        
        QMessageBox.about(self, "ℹ️ GymTrackerについて", about_text)
    
    def closeEvent(self, event):
        """アプリケーション終了時の処理"""
        try:
            reply = QMessageBox.question(
                self, "🚪 終了確認", 
                "アプリケーションを終了しますか？\n\n"
                "💾 未保存のデータがある場合は保存されます。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("Application closing by user request")
                
                # リソースのクリーンアップ
                try:
                    # matplotlib のクリーンアップ
                    if hasattr(self, 'stats_tab') and hasattr(self.stats_tab, 'figure'):
                        import matplotlib.pyplot as plt
                        plt.close('all')
                except Exception as e:
                    self.logger.warning(f"Matplotlib cleanup failed: {e}")
                
                try:
                    # データベース接続のクリーンアップ
                    if hasattr(self, 'db_manager'):
                        # 最後のバックアップ（オプション）
                        if hasattr(self.db_manager, 'backup_database'):
                            self.db_manager.backup_database()
                except Exception as e:
                    self.logger.warning(f"Database cleanup failed: {e}")
                
                self.statusBar().showMessage("👋 また会いましょう！", 1000)
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            self.logger.error(f"Close event failed: {e}")
            # エラーが発生しても終了は許可
            event.accept()