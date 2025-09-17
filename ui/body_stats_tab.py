# ui/body_stats_tab.py - 最適化版（高速化対応）
from typing import List, Dict, Optional, Any, Union
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QComboBox, QLabel, 
                               QPushButton, QHeaderView, QSplitter,
                               QGroupBox, QFrame, QDialog, QMessageBox,
                               QWidget, QProgressBar)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont

from .base_tab import BaseTab
from database.models import BodyStats

# matplotlibのインポートと型安全性
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
    
    # matplotlib設定の最適化
    plt.rcParams['figure.max_open_warning'] = 0  # 警告抑制
    plt.rcParams['agg.path.chunksize'] = 10000   # 描画最適化
    
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class DataLoadThread(QThread):
    """データ読み込み用スレッド"""
    data_loaded = Signal(list)  # type: ignore
    summary_loaded = Signal(dict)  # type: ignore
    error_occurred = Signal(str)  # type: ignore
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager

        import logging
        self.logger = logging.getLogger(__name__)

        if not hasattr(db_manager, 'get_body_stats_optimized'):
            self.logger.warning("get_body_stats_optimized not found, using fallback")
            db_manager.get_body_stats_optimized = db_manager.get_all_body_stats
        
        if not hasattr(db_manager, 'get_body_stats_summary_optimized'):
            self.logger.warning("get_body_stats_summary_optimized not found, using fallback")
            db_manager.get_body_stats_summary_optimized = db_manager.get_body_stats_summary
    
    def run(self):
        """バックグラウンドでデータ読み込み"""
        try:
            # データ読み込み（最適化クエリ使用）
            stats_list = self.db_manager.get_body_stats_optimized()
            self.data_loaded.emit(stats_list)
            
            # サマリー読み込み
            summary = self.db_manager.get_body_stats_summary_optimized()
            self.summary_loaded.emit(summary)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class BodyStatsTab(BaseTab):
    """体組成管理タブ - 最適化版"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        
        # データキャッシュ
        self._cached_data: List[BodyStats] = []
        self._cached_summary: Dict = {}
        self._data_loaded = False
        
        # UI初期化（軽量版）
        self.init_ui_fast()
        
        # バックグラウンドデータ読み込み
        self.load_data_async()
    
    def init_ui_fast(self):
        """UI初期化（高速版）"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("📊 体組成管理")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: #2c3e50; }")
        layout.addWidget(title_label)
        
        # ローディング表示
        self.loading_frame = self.create_loading_frame()
        layout.addWidget(self.loading_frame)
        
        # メインコンテンツ（初期は非表示）
        self.main_content = QWidget()
        self.setup_main_content()
        self.main_content.setVisible(False)
        layout.addWidget(self.main_content)
    
    def create_loading_frame(self) -> QFrame:
        """ローディング画面"""
        loading_frame = QFrame()
        loading_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
            }
        """)
        
        layout = QVBoxLayout(loading_frame)
        
        # ローディングメッセージ
        loading_label = QLabel("📊 体組成データを読み込み中...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("font-size: 16px; color: #495057; margin: 20px;")
        layout.addWidget(loading_label)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # インデターミネート
        layout.addWidget(self.progress_bar)
        
        return loading_frame
    
    def setup_main_content(self):
        """メインコンテンツ設定"""
        layout = QVBoxLayout(self.main_content)
        
        # サマリーエリア
        self.summary_frame = self.create_summary_area()
        layout.addWidget(self.summary_frame)
        
        # メインエリア（スプリッター）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：データ管理エリア
        data_widget = self.create_data_area()
        splitter.addWidget(data_widget)
        
        # 右側：グラフエリア
        if MATPLOTLIB_AVAILABLE:
            graph_widget = self.create_graph_area()
            splitter.addWidget(graph_widget)
        else:
            placeholder = self.create_matplotlib_placeholder()
            splitter.addWidget(placeholder)
        
        # スプリッター比率設定
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def load_data_async(self):
        """非同期データ読み込み"""
        # データ読み込みスレッド開始
        self.data_thread = DataLoadThread(self.db_manager)
        self.data_thread.data_loaded.connect(self.on_data_loaded)
        self.data_thread.summary_loaded.connect(self.on_summary_loaded)
        self.data_thread.error_occurred.connect(self.on_load_error)
        self.data_thread.start()
    
    def on_data_loaded(self, stats_list: List[BodyStats]):
        """データ読み込み完了"""
        self._cached_data = stats_list
        self.populate_table_fast(stats_list)
        self._data_loaded = True
        
        # グラフ更新（遅延実行）
        QTimer.singleShot(100, self.update_graph)
    
    def on_summary_loaded(self, summary: Dict):
        """サマリー読み込み完了"""
        self._cached_summary = summary
        self.update_summary_fast(summary)
        
        # UI切り替え
        self.loading_frame.setVisible(False)
        self.main_content.setVisible(True)
    
    def on_load_error(self, error_message: str):
        """データ読み込みエラー"""
        self.loading_frame.setVisible(False)
        self.show_error("データ読み込みエラー", "体組成データの読み込みに失敗しました", error_message)
        
        # エラー時もメインコンテンツを表示
        self.main_content.setVisible(True)
    
    def create_summary_area(self) -> QFrame:
        """サマリーエリア作成"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(summary_frame)
        
        # 現在の値表示エリア
        self.current_weight_label = QLabel("⚖️ 体重: --")
        self.current_weight_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.current_weight_label)
        
        layout.addWidget(QLabel("|"))
        
        self.current_body_fat_label = QLabel("📈 体脂肪率: --")
        self.current_body_fat_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.current_body_fat_label)
        
        layout.addWidget(QLabel("|"))
        
        self.current_muscle_label = QLabel("💪 筋肉量: --")
        self.current_muscle_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        layout.addWidget(self.current_muscle_label)
        
        layout.addStretch()
        
        # 変化量表示エリア
        self.change_label = QLabel("📊 変化量: --")
        self.change_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        layout.addWidget(self.change_label)
        
        return summary_frame
    
    def create_data_area(self) -> QGroupBox:
        """データ管理エリア作成"""
        data_widget = QGroupBox("📋 データ管理")
        layout = QVBoxLayout(data_widget)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ 記録追加")
        self.add_button.clicked.connect(self.add_body_stats)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("✏️ 編集")
        self.edit_button.clicked.connect(self.edit_selected_stats)
        self.edit_button.setEnabled(False)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("🗑️ 削除")
        self.delete_button.clicked.connect(self.delete_selected_stats)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # データテーブル
        self.stats_table = QTableWidget()
        self.setup_table_fast()
        layout.addWidget(self.stats_table)
        
        return data_widget
    
    def setup_table_fast(self):
        """テーブル設定（最適化版）"""
        columns = ["日付", "体重", "体脂肪率", "筋肉量", "BMI"]
        self.stats_table.setColumnCount(len(columns))
        self.stats_table.setHorizontalHeaderLabels(columns)
        
        # 列幅設定
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 日付
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 体重
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 体脂肪率
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 筋肉量
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # BMI
        
        # テーブル設定（最適化）
        self.stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setSortingEnabled(False)  # 初期読み込み時はソート無効
        self.stats_table.itemSelectionChanged.connect(self.update_button_states)
        
        # パフォーマンス最適化
        self.stats_table.setUpdatesEnabled(False)  # 更新を一時停止
        
        # ヘッダースタイル
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: 1px solid #2c3e50;
                font-weight: bold;
            }
        """)
    
    def populate_table_fast(self, stats_list: List[BodyStats]):
        """テーブル高速描画"""
        if not stats_list:
            self.stats_table.setUpdatesEnabled(True)
            return
        
        self.stats_table.setRowCount(len(stats_list))
        
        # バッチでアイテムを設定（高速化）
        for row, stats in enumerate(stats_list):
            # 日付
            date_item = QTableWidgetItem(str(stats.date))
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            date_item.setData(Qt.ItemDataRole.UserRole, stats)
            self.stats_table.setItem(row, 0, date_item)
            
            # 体重
            weight_text = f"{stats.weight:.1f}kg" if stats.weight else "--"
            weight_item = QTableWidgetItem(weight_text)
            weight_item.setFlags(weight_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 1, weight_item)
            
            # 体脂肪率
            body_fat_text = f"{stats.body_fat_percentage:.1f}%" if stats.body_fat_percentage else "--"
            body_fat_item = QTableWidgetItem(body_fat_text)
            body_fat_item.setFlags(body_fat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            body_fat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 2, body_fat_item)
            
            # 筋肉量
            muscle_text = f"{stats.muscle_mass:.1f}kg" if stats.muscle_mass else "--"
            muscle_item = QTableWidgetItem(muscle_text)
            muscle_item.setFlags(muscle_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            muscle_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 3, muscle_item)
            
            # BMI計算（仮の身長185cmで計算）
            if stats.weight:
                bmi = stats.weight / (1.85 ** 2)
                bmi_text = f"{bmi:.1f}"
                if bmi < 18.5:
                    bmi_text += " (低体重)"
                elif bmi < 25:
                    bmi_text += " (標準)"
                else:
                    bmi_text += " (肥満)"
            else:
                bmi_text = "--"
            
            bmi_item = QTableWidgetItem(bmi_text)
            bmi_item.setFlags(bmi_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            bmi_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_table.setItem(row, 4, bmi_item)
        
        # 更新を再開
        self.stats_table.setUpdatesEnabled(True)
        
        # ソートを有効化
        self.stats_table.setSortingEnabled(True)
        self.stats_table.sortItems(0, Qt.SortOrder.DescendingOrder)  # 日付降順
    
    def update_summary_fast(self, summary: Dict):
        """サマリー高速更新"""
        # 現在の値
        if summary.get('current_weight'):
            self.current_weight_label.setText(f"⚖️ 体重: {summary['current_weight']:.1f}kg")
        else:
            self.current_weight_label.setText("⚖️ 体重: --")
        
        if summary.get('current_body_fat'):
            self.current_body_fat_label.setText(f"📈 体脂肪率: {summary['current_body_fat']:.1f}%")
        else:
            self.current_body_fat_label.setText("📈 体脂肪率: --")
        
        if summary.get('current_muscle'):
            self.current_muscle_label.setText(f"💪 筋肉量: {summary['current_muscle']:.1f}kg")
        else:
            self.current_muscle_label.setText("💪 筋肉量: --")
        
        # 変化量
        changes = []
        if summary.get('weight_change_month') is not None:
            change = summary['weight_change_month']
            changes.append(f"体重: {change:+.1f}kg")
        
        if summary.get('body_fat_change_month') is not None:
            change = summary['body_fat_change_month']
            changes.append(f"体脂肪率: {change:+.1f}%")
        
        if summary.get('muscle_change_month') is not None:
            change = summary['muscle_change_month']
            changes.append(f"筋肉量: {change:+.1f}kg")
        
        if changes:
            self.change_label.setText(f"📊 前月比: {', '.join(changes)}")
        else:
            self.change_label.setText("📊 変化量: --")
    
    def create_graph_area(self) -> QWidget:
        """グラフエリア作成"""
        if not MATPLOTLIB_AVAILABLE:
            return self.create_matplotlib_placeholder()
        
        graph_widget = QGroupBox("📈 推移グラフ")
        layout = QVBoxLayout(graph_widget)
        
        # グラフ種類選択
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("表示項目:"))
        
        self.graph_type = QComboBox()
        self.graph_type.addItem("⚖️ 体重推移", "weight")
        self.graph_type.addItem("📈 体脂肪率推移", "body_fat")
        self.graph_type.addItem("💪 筋肉量推移", "muscle")
        self.graph_type.addItem("📊 全項目比較", "all")
        self.graph_type.currentTextChanged.connect(self.on_graph_type_changed)
        control_layout.addWidget(self.graph_type)
        
        # 期間選択
        control_layout.addWidget(QLabel("期間:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("過去1ヶ月", 30)
        self.period_combo.addItem("過去3ヶ月", 90)
        self.period_combo.addItem("過去6ヶ月", 180)
        self.period_combo.addItem("過去1年", 365)
        self.period_combo.addItem("全期間", -1)
        self.period_combo.setCurrentIndex(2)  # デフォルトは6ヶ月
        self.period_combo.currentTextChanged.connect(self.on_graph_type_changed)
        control_layout.addWidget(self.period_combo)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # グラフ（軽量初期化）
        self.figure = Figure(figsize=(10, 6), dpi=80)  # DPI下げて軽量化
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        return graph_widget
    
    def on_graph_type_changed(self):
        """グラフタイプ変更時（遅延実行）"""
        # 頻繁な更新を避けるため、タイマーで遅延実行
        if hasattr(self, '_graph_timer'):
            self._graph_timer.stop()
        
        self._graph_timer = QTimer()
        self._graph_timer.setSingleShot(True)
        self._graph_timer.timeout.connect(self.update_graph)
        self._graph_timer.start(300)  # 300ms後に実行
    
    def update_graph(self):
        """グラフ更新（最適化版）"""
        if not MATPLOTLIB_AVAILABLE or not self._data_loaded:
            return
        
        try:
            graph_type = self.graph_type.currentData()
            period_days = self.period_combo.currentData()
            
            # キャッシュからデータ取得
            stats_list = self._cached_data
            
            # 期間フィルタリング
            if period_days > 0 and stats_list:
                cutoff_date = date.today() - timedelta(days=period_days)
                stats_list = [s for s in stats_list 
                             if (isinstance(s.date, date) and s.date >= cutoff_date) or
                                (isinstance(s.date, str) and datetime.strptime(s.date, '%Y-%m-%d').date() >= cutoff_date)]
            
            if not stats_list:
                self.show_empty_graph()
                return
            
            # 日付順にソート
            stats_list.sort(key=lambda x: x.date if isinstance(x.date, date) else datetime.strptime(x.date, '%Y-%m-%d').date())
            
            # グラフ描画（最適化）
            self.figure.clear()
            
            if graph_type == "weight":
                self.plot_weight_progress_fast(stats_list)
            elif graph_type == "body_fat":
                self.plot_body_fat_progress_fast(stats_list)
            elif graph_type == "muscle":
                self.plot_muscle_progress_fast(stats_list)
            elif graph_type == "all":
                self.plot_all_progress_fast(stats_list)
            
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Graph update error: {e}")
            self.show_error_graph(str(e))
    
    def show_empty_graph(self):
        """データなしグラフ表示"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '📊 データがありません\n\n体組成データを記録してください',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=14, color='#95a5a6')
        self.canvas.draw()
    
    def show_error_graph(self, error_message: str):
        """エラーグラフ表示"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, f'❌ グラフの描画に失敗しました:\n{error_message}',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=12, color='red')
        self.canvas.draw()
    
    def plot_weight_progress_fast(self, stats_list: List[BodyStats]):
        """体重推移グラフ（最適化版）"""
        ax = self.figure.add_subplot(111)
        
        # データ準備
        dates = []
        weights = []
        
        for stats in stats_list:
            if stats.weight is not None:
                if isinstance(stats.date, str):
                    dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    dates.append(datetime.combine(stats.date, datetime.min.time()))
                weights.append(float(stats.weight))
        
        if dates and weights:
            # 最適化されたプロット
            ax.plot(dates, weights, marker='o', linewidth=2, markersize=4,
                   color='#3498db', markerfacecolor='#2980b9', alpha=0.8)
            
            ax.set_title('⚖️ 体重推移', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('体重 (kg)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        self.format_date_axis_fast(ax, dates)
    
    def plot_body_fat_progress_fast(self, stats_list: List[BodyStats]):
        """体脂肪率推移グラフ（最適化版）"""
        ax = self.figure.add_subplot(111)
        
        dates = []
        body_fats = []
        
        for stats in stats_list:
            if stats.body_fat_percentage is not None:
                if isinstance(stats.date, str):
                    dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    dates.append(datetime.combine(stats.date, datetime.min.time()))
                body_fats.append(float(stats.body_fat_percentage))
        
        if dates and body_fats:
            ax.plot(dates, body_fats, marker='s', linewidth=2, markersize=4,
                   color='#e74c3c', markerfacecolor='#c0392b', alpha=0.8)
            
            ax.set_title('📈 体脂肪率推移', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('体脂肪率 (%)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        self.format_date_axis_fast(ax, dates)
    
    def plot_muscle_progress_fast(self, stats_list: List[BodyStats]):
        """筋肉量推移グラフ（最適化版）"""
        ax = self.figure.add_subplot(111)
        
        dates = []
        muscles = []
        
        for stats in stats_list:
            if stats.muscle_mass is not None:
                if isinstance(stats.date, str):
                    dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    dates.append(datetime.combine(stats.date, datetime.min.time()))
                muscles.append(float(stats.muscle_mass))
        
        if dates and muscles:
            ax.plot(dates, muscles, marker='^', linewidth=2, markersize=4,
                   color='#27ae60', markerfacecolor='#229954', alpha=0.8)
            
            ax.set_title('💪 筋肉量推移', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('筋肉量 (kg)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        self.format_date_axis_fast(ax, dates)
    
    def plot_all_progress_fast(self, stats_list: List[BodyStats]):
        """全項目推移グラフ（最適化版）"""
        ax1 = self.figure.add_subplot(111)
        
        # 体重データ（左軸）
        weight_dates = []
        weights = []
        
        for stats in stats_list:
            if stats.weight is not None:
                if isinstance(stats.date, str):
                    weight_dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    weight_dates.append(datetime.combine(stats.date, datetime.min.time()))
                weights.append(float(stats.weight))
        
        if weight_dates and weights:
            ax1.plot(weight_dates, weights, marker='o', linewidth=2, markersize=3,
                    color='#3498db', label='体重 (kg)', alpha=0.8)
            ax1.set_ylabel('体重 (kg)', fontsize=12, color='#3498db')
            ax1.tick_params(axis='y', labelcolor='#3498db')
        
        # 体脂肪率・筋肉量（右軸）
        ax2 = ax1.twinx()
        
        # 体脂肪率データ
        body_fat_dates = []
        body_fats = []
        
        for stats in stats_list:
            if stats.body_fat_percentage is not None:
                if isinstance(stats.date, str):
                    body_fat_dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    body_fat_dates.append(datetime.combine(stats.date, datetime.min.time()))
                body_fats.append(float(stats.body_fat_percentage))
        
        if body_fat_dates and body_fats:
            ax2.plot(body_fat_dates, body_fats, marker='s', linewidth=2, markersize=3,
                   color='#e74c3c', label='体脂肪率 (%)', alpha=0.8)
        
        # 筋肉量データ
        muscle_dates = []
        muscles = []
        
        for stats in stats_list:
            if stats.muscle_mass is not None:
                if isinstance(stats.date, str):
                    muscle_dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    muscle_dates.append(datetime.combine(stats.date, datetime.min.time()))
                muscles.append(float(stats.muscle_mass))
        
        if muscle_dates and muscles:
            ax2.plot(muscle_dates, muscles, marker='^', linewidth=2, markersize=3,
                   color='#27ae60', label='筋肉量 (kg)', alpha=0.8)
        
        ax2.set_ylabel('体脂肪率 (%) / 筋肉量 (kg)', fontsize=12)
        
        # 凡例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
        
        ax1.set_title('📊 体組成推移（全項目）', fontsize=14, fontweight='bold', color='#2c3e50')
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        all_dates = weight_dates if weight_dates else (body_fat_dates if body_fat_dates else muscle_dates)
        self.format_date_axis_fast(ax1, all_dates)
    
    def format_date_axis_fast(self, ax, dates: List[datetime]):
        """日付軸のフォーマット（最適化版）"""
        if not dates:
            return
        
        ax.set_xlabel('日付', fontsize=12)
        
        # データ数に応じて間隔調整
        if len(dates) > 20:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        elif len(dates) > 10:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # 回転角度を最小限に
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)
    
    def create_matplotlib_placeholder(self) -> QWidget:
        """matplotlib未インストール時のプレースホルダー"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        
        message = QLabel("""
📊 グラフ表示機能

❌ matplotlibが必要です

💻 インストール方法：
pip install matplotlib

📈 利用可能になる機能：
• 体重推移グラフ
• 体脂肪率推移
• 筋肉量変化グラフ
• 全項目比較グラフ
        """)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 2px dashed #e74c3c;
                margin: 20px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(message)
        
        return placeholder
    
    def add_body_stats(self):
        """体組成データ追加"""
        from .body_stats_dialog import BodyStatsDialog
        
        dialog = BodyStatsDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            stats_data = dialog.get_body_stats()
            
            # 入力値検証
            if not stats_data.weight:
                self.show_warning("入力エラー", "体重を入力してください。")
                return
            
            # 同日データの重複チェック
            existing = self.db_manager.get_body_stats_by_date(stats_data.date)
            if existing:
                reply = QMessageBox.question(self, "重複確認", 
                                           f"{stats_data.date}のデータは既に存在します。\n"
                                           "上書きしますか？",
                                           QMessageBox.StandardButton.Yes | 
                                           QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    stats_data.id = existing.id
                    if self.db_manager.update_body_stats(stats_data):
                        self.show_info("更新完了", "✅ 体組成データを更新しました！")
                    else:
                        self.show_error("更新エラー", "データの更新に失敗しました。")
                else:
                    return
            else:
                # 新規追加
                stats_id = self.db_manager.add_body_stats(stats_data)
                if stats_id:
                    self.show_info("記録完了", "✅ 体組成データを記録しました！")
                else:
                    self.show_error("保存エラー", "データの保存に失敗しました。")
            
            # データ再読み込み（非同期）
            self.refresh_data()
    
    def edit_selected_stats(self):
        """選択された体組成データを編集"""
        current_row = self.stats_table.currentRow()
        if current_row < 0:
            return
        
        date_item = self.stats_table.item(current_row, 0)
        if not date_item:
            return
        
        stats = date_item.data(Qt.ItemDataRole.UserRole)
        if not stats:
            return
        
        from .body_stats_dialog import BodyStatsDialog
        
        dialog = BodyStatsDialog(self.db_manager, stats, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_stats = dialog.get_body_stats()
            
            if self.db_manager.update_body_stats(updated_stats):
                self.show_info("更新完了", "✅ 体組成データを更新しました！")
                self.refresh_data()
            else:
                self.show_error("更新エラー", "データの更新に失敗しました。")
    
    def delete_selected_stats(self):
        """選択された体組成データを削除"""
        current_row = self.stats_table.currentRow()
        if current_row < 0:
            return
        
        date_item = self.stats_table.item(current_row, 0)
        if not date_item:
            return
        
        stats = date_item.data(Qt.ItemDataRole.UserRole)
        if not stats:
            return
        
        reply = QMessageBox.question(self, "🗑️ 削除確認",
                                   f"{stats.date}の体組成データを削除しますか？\n\n"
                                   f"⚠️ この操作は取り消せません。",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_body_stats(stats.id):
                self.show_info("削除完了", "🗑️ 体組成データを削除しました。")
                self.refresh_data()
            else:
                self.show_error("削除エラー", "データの削除に失敗しました。")
    
    def update_button_states(self):
        """ボタン状態更新"""
        has_selection = self.stats_table.currentRow() >= 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def refresh_data(self):
        """データ再読み込み（外部から呼び出し用）"""
        self._data_loaded = False
        self.loading_frame.setVisible(True)
        self.main_content.setVisible(False)
        self.load_data_async()