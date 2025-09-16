# ui/stats_tab.py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
                               QTableWidget, QTableWidgetItem, QSplitter,
                               QHeaderView, QWidget, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt

from .base_tab import BaseTab

# matplotlib日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']

class StatsTab(BaseTab):
    """統計タブ"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_exercises()
        self.setup_graph()
    
    def init_ui(self) -> None:
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("トレーニング統計")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; margin-bottom: 10px; }")
        layout.addWidget(title_label)
        
        # 控制区域
        control_group = self.create_control_area()
        layout.addWidget(control_group)
        
        # メインエリア（スプリッター）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # グラフエリア
        graph_widget = self.create_graph_area()
        splitter.addWidget(graph_widget)
        
        # 統計テーブル
        stats_widget = self.create_stats_area()
        splitter.addWidget(stats_widget)
        
        # スプリッター比率設定
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)
    
    def create_control_area(self) -> QGroupBox:
        """コントロールエリア作成"""
        control_group = QGroupBox("グラフ設定")
        control_layout = QVBoxLayout(control_group)
        
        # 1行目: グラフ種類と種目
        row1_layout = QHBoxLayout()
        
        # グラフ種類選択
        row1_layout.addWidget(QLabel("グラフ種類:"))
        self.graph_type = QComboBox()
        self.graph_type.addItem("1RM推移", "one_rm_progress")
        self.graph_type.addItem("重量推移", "weight_progress")  
        self.graph_type.addItem("ボリューム推移", "volume_progress")
        self.graph_type.addItem("頻度分析", "frequency_analysis")
        self.graph_type.addItem("部位別分析", "category_analysis")
        self.graph_type.currentTextChanged.connect(self.update_graph)
        row1_layout.addWidget(self.graph_type)
        
        # 種目選択
        row1_layout.addWidget(QLabel("種目:"))
        self.exercise_combo = QComboBox()
        self.exercise_combo.currentTextChanged.connect(self.update_graph)
        row1_layout.addWidget(self.exercise_combo)
        
        row1_layout.addStretch()
        control_layout.addLayout(row1_layout)
        
        # 2行目: 期間選択
        row2_layout = QHBoxLayout()
        
        row2_layout.addWidget(QLabel("期間:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("過去1ヶ月", 30)
        self.period_combo.addItem("過去3ヶ月", 90)
        self.period_combo.addItem("過去6ヶ月", 180)
        self.period_combo.addItem("過去1年", 365)
        self.period_combo.addItem("全期間", -1)
        self.period_combo.setCurrentIndex(2)  # デフォルトは過去6ヶ月
        self.period_combo.currentTextChanged.connect(self.update_graph)
        row2_layout.addWidget(self.period_combo)
        
        row2_layout.addStretch()
        control_layout.addLayout(row2_layout)
        
        return control_group
    
    def create_graph_area(self) -> QWidget:
        """グラフエリア作成"""
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        graph_layout.addWidget(self.canvas)
        
        return graph_widget
    
    def create_stats_area(self) -> QWidget:
        """統計エリア作成"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # 統計テーブルのタイトル
        stats_title = QLabel("統計情報")
        stats_title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        stats_layout.addWidget(stats_title)
        
        # 統計テーブル
        self.stats_table = QTableWidget()
        self.setup_stats_table()
        stats_layout.addWidget(self.stats_table)
        
        return stats_widget
    
    def setup_stats_table(self) -> None:
        """統計テーブル設定"""
        columns = ["項目", "値"]
        self.stats_table.setColumnCount(len(columns))
        self.stats_table.setHorizontalHeaderLabels(columns)
        
        # 列幅設定
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.stats_table.setAlternatingRowColors(True)
        
        # ヘッダースタイル
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def load_exercises(self) -> None:
        """種目読み込み"""
        try:
            exercises = self.db_manager.get_all_exercises()
            self.exercise_combo.clear()
            self.exercise_combo.addItem("種目を選択してください", None)
            
            # カテゴリ別に整理
            categories = {}
            for exercise in exercises:
                if exercise.category not in categories:
                    categories[exercise.category] = []
                categories[exercise.category].append(exercise)
            
            # カテゴリ順で追加
            for category in ["胸", "背中", "脚", "肩", "腕"]:
                if category in categories:
                    for exercise in categories[category]:
                        self.exercise_combo.addItem(exercise.display_name(), exercise.id)
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "種目データの読み込みに失敗しました", str(e))
    
    def setup_graph(self) -> None:
        """グラフ初期設定"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '種目を選択してグラフを表示',
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        self.canvas.draw()
    
    def update_graph(self) -> None:
        """グラフ更新（エラー処理付き）"""
        try:
            graph_type = self.graph_type.currentData()
            exercise_id = self.exercise_combo.currentData()
            period_days = self.period_combo.currentData()
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            try:
                if graph_type == "one_rm_progress":
                    if exercise_id is None:
                        ax.text(0.5, 0.5, '種目を選択してください',
                                ha='center', va='center', transform=ax.transAxes)
                    else:
                        self.plot_one_rm_progress(ax, exercise_id, period_days)
                elif graph_type == "weight_progress":
                    if exercise_id is None:
                        ax.text(0.5, 0.5, '種目を選択してください',
                                ha='center', va='center', transform=ax.transAxes)
                    else:
                        self.plot_weight_progress(ax, exercise_id, period_days)
                elif graph_type == "volume_progress":
                    if exercise_id is None:
                        ax.text(0.5, 0.5, '種目を選択してください',
                                ha='center', va='center', transform=ax.transAxes)
                    else:
                        self.plot_volume_progress(ax, exercise_id, period_days)
                elif graph_type == "frequency_analysis":
                    self.plot_frequency_analysis(ax, period_days)
                elif graph_type == "category_analysis":
                    self.plot_category_analysis(ax, period_days)
                
                self.figure.tight_layout()
                
                # 統計テーブル更新
                self.update_stats_table(graph_type, exercise_id, period_days)
                
            except Exception as plot_error:
                ax.clear()
                ax.text(0.5, 0.5, f'グラフの描画に失敗しました:\n{str(plot_error)}',
                        ha='center', va='center', transform=ax.transAxes)
                self.logger.error(f"Plot error: {plot_error}")
            
            try:
                self.canvas.draw()
            except Exception as draw_error:
                self.logger.error(f"Canvas draw error: {draw_error}")
                self.show_warning("描画エラー", "グラフの描画でエラーが発生しました")
                
        except Exception as e:
            self.logger.error(f"Graph update error: {e}")
            self.show_error("グラフエラー", f"グラフの更新に失敗しました: {e}")
    
    def get_exercise_data(self, exercise_id: int, period_days: int) -> List[Tuple]:
        """種目データ取得"""
        try:
            end_date = date.today()
            if period_days > 0:
                start_date = end_date - timedelta(days=period_days)
            else:
                start_date = None
            
            with self.db_manager.get_connection() as conn:
                if start_date:
                    query = """
                        SELECT w.date, s.weight, s.reps, s.one_rm, s.set_number
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        WHERE s.exercise_id = ? AND w.date >= ?
                        ORDER BY w.date, s.set_number
                    """
                    cursor = conn.execute(query, (exercise_id, start_date))
                else:
                    query = """
                        SELECT w.date, s.weight, s.reps, s.one_rm, s.set_number
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        WHERE s.exercise_id = ?
                        ORDER BY w.date, s.set_number
                    """
                    cursor = conn.execute(query, (exercise_id,))
                
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to get exercise data: {e}")
            return []
    
    def plot_one_rm_progress(self, ax, exercise_id: int, period_days: int) -> None:
        """1RM推移グラフ"""
        data = self.get_exercise_data(exercise_id, period_days)
        
        if not data:
            ax.text(0.5, 0.5, 'データがありません',
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # 日付ごとの最大1RMを計算
        daily_max_1rm = {}
        for row in data:
            workout_date = datetime.strptime(str(row[0]), '%Y-%m-%d').date()
            one_rm = float(row[3]) if row[3] else 0
            
            if workout_date not in daily_max_1rm:
                daily_max_1rm[workout_date] = one_rm
            else:
                daily_max_1rm[workout_date] = max(daily_max_1rm[workout_date], one_rm)
        
        # データをソートして描画
        dates = sorted(daily_max_1rm.keys())
        one_rms = [daily_max_1rm[d] for d in dates]
        
        if dates:
            ax.plot(dates, one_rms, marker='o', linewidth=2, markersize=6, color='#2E86C1')
            ax.set_title('1RM推移', fontsize=14, fontweight='bold')
            ax.set_xlabel('日付')
            ax.set_ylabel('1RM (kg)')
            ax.grid(True, alpha=0.3)
            
            # 日付フォーマット
            if len(dates) > 10:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_weight_progress(self, ax, exercise_id: int, period_days: int) -> None:
        """重量推移グラフ"""
        data = self.get_exercise_data(exercise_id, period_days)
        
        if not data:
            ax.text(0.5, 0.5, 'データがありません',
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # 日付ごとの最大重量を計算
        daily_max_weight = {}
        for row in data:
            workout_date = datetime.strptime(str(row[0]), '%Y-%m-%d').date()
            weight = float(row[1])
            
            if workout_date not in daily_max_weight:
                daily_max_weight[workout_date] = weight
            else:
                daily_max_weight[workout_date] = max(daily_max_weight[workout_date], weight)
        
        # データをソートして描画
        dates = sorted(daily_max_weight.keys())
        weights = [daily_max_weight[d] for d in dates]
        
        if dates:
            ax.plot(dates, weights, marker='s', linewidth=2, markersize=6, color='#F39C12')
            ax.set_title('重量推移', fontsize=14, fontweight='bold')
            ax.set_xlabel('日付')
            ax.set_ylabel('重量 (kg)')
            ax.grid(True, alpha=0.3)
            
            # 日付フォーマット
            if len(dates) > 10:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_volume_progress(self, ax, exercise_id: int, period_days: int) -> None:
        """ボリューム推移グラフ"""
        data = self.get_exercise_data(exercise_id, period_days)
        
        if not data:
            ax.text(0.5, 0.5, 'データがありません',
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # 日付ごとの総ボリュームを計算
        daily_volume = {}
        for row in data:
            workout_date = datetime.strptime(str(row[0]), '%Y-%m-%d').date()
            volume = float(row[1]) * int(row[2])  # 重量 × 回数
            
            if workout_date not in daily_volume:
                daily_volume[workout_date] = volume
            else:
                daily_volume[workout_date] += volume
        
        # データをソートして描画
        dates = sorted(daily_volume.keys())
        volumes = [daily_volume[d] for d in dates]
        
        if dates:
            ax.bar(dates, volumes, width=1, alpha=0.7, color='#28B463')
            ax.set_title('トレーニングボリューム推移', fontsize=14, fontweight='bold')
            ax.set_xlabel('日付')
            ax.set_ylabel('ボリューム (kg)')
            ax.grid(True, alpha=0.3, axis='y')
            
            # 日付フォーマット
            if len(dates) > 10:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_frequency_analysis(self, ax, period_days: int) -> None:
        """頻度分析グラフ"""
        try:
            end_date = date.today()
            if period_days > 0:
                start_date = end_date - timedelta(days=period_days)
            else:
                start_date = None
                
            with self.db_manager.get_connection() as conn:
                if start_date:
                    query = """
                        SELECT e.category, COUNT(DISTINCT w.date) as workout_days
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        JOIN exercises e ON s.exercise_id = e.id
                        WHERE w.date >= ?
                        GROUP BY e.category
                        ORDER BY workout_days DESC
                    """
                    cursor = conn.execute(query, (start_date,))
                else:
                    query = """
                        SELECT e.category, COUNT(DISTINCT w.date) as workout_days
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        JOIN exercises e ON s.exercise_id = e.id
                        GROUP BY e.category
                        ORDER BY workout_days DESC
                    """
                    cursor = conn.execute(query)
                
                results = cursor.fetchall()
                
                if results:
                    categories = [row[0] for row in results]
                    frequencies = [row[1] for row in results]
                    
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                    bars = ax.bar(categories, frequencies, color=colors[:len(categories)])
                    
                    ax.set_title('部位別トレーニング頻度', fontsize=14, fontweight='bold')
                    ax.set_xlabel('筋肉部位')
                    ax.set_ylabel('トレーニング日数')
                    ax.grid(True, alpha=0.3, axis='y')
                    
                    # 棒グラフに値を表示
                    for bar, freq in zip(bars, frequencies):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                               f'{freq}日', ha='center', va='bottom')
                else:
                    ax.text(0.5, 0.5, 'データがありません',
                            ha='center', va='center', transform=ax.transAxes)
                    
        except Exception as e:
            self.logger.error(f"Frequency analysis error: {e}")
            ax.text(0.5, 0.5, 'データの取得に失敗しました',
                    ha='center', va='center', transform=ax.transAxes)
    
    def plot_category_analysis(self, ax, period_days: int) -> None:
        """部位別分析グラフ（円グラフ）"""
        try:
            end_date = date.today()
            if period_days > 0:
                start_date = end_date - timedelta(days=period_days)
            else:
                start_date = None
                
            with self.db_manager.get_connection() as conn:
                if start_date:
                    query = """
                        SELECT e.category, COUNT(s.id) as set_count
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        JOIN exercises e ON s.exercise_id = e.id
                        WHERE w.date >= ?
                        GROUP BY e.category
                        ORDER BY set_count DESC
                    """
                    cursor = conn.execute(query, (start_date,))
                else:
                    query = """
                        SELECT e.category, COUNT(s.id) as set_count
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        JOIN exercises e ON s.exercise_id = e.id
                        GROUP BY e.category
                        ORDER BY set_count DESC
                    """
                    cursor = conn.execute(query)
                
                results = cursor.fetchall()
                
                if results:
                    categories = [row[0] for row in results]
                    set_counts = [row[1] for row in results]
                    
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
                    
                    wedges, texts, autotexts = ax.pie(set_counts, labels=categories, 
                                                     autopct='%1.1f%%', startangle=90,
                                                     colors=colors[:len(categories)])
                    
                    ax.set_title('部位別セット数の割合', fontsize=14, fontweight='bold')
                    
                    # テキストのフォントサイズ調整
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                        autotext.set_fontsize(9)
                else:
                    ax.text(0.5, 0.5, 'データがありません',
                            ha='center', va='center', transform=ax.transAxes)
                    
        except Exception as e:
            self.logger.error(f"Category analysis error: {e}")
            ax.text(0.5, 0.5, 'データの取得に失敗しました',
                    ha='center', va='center', transform=ax.transAxes)
    
    def update_stats_table(self, graph_type: str, exercise_id: Optional[int], period_days: int) -> None:
        """統計テーブル更新"""
        try:
            stats_data = []
            
            if graph_type in ["one_rm_progress", "weight_progress", "volume_progress"] and exercise_id:
                # 種目別統計
                data = self.get_exercise_data(exercise_id, period_days)
                if data:
                    weights = [float(row[1]) for row in data]
                    one_rms = [float(row[3]) for row in data if row[3]]
                    volumes = [float(row[1]) * int(row[2]) for row in data]
                    
                    stats_data = [
                        ("総セット数", f"{len(data)}セット"),
                        ("最大重量", f"{max(weights):.1f}kg"),
                        ("平均重量", f"{sum(weights)/len(weights):.1f}kg"),
                        ("最大1RM", f"{max(one_rms):.1f}kg" if one_rms else "N/A"),
                        ("総ボリューム", f"{sum(volumes):.0f}kg"),
                        ("平均ボリューム/セット", f"{sum(volumes)/len(volumes):.1f}kg"),
                    ]
            else:
                # 全体統計
                with self.db_manager.get_connection() as conn:
                    end_date = date.today()
                    if period_days > 0:
                        start_date = end_date - timedelta(days=period_days)
                        query = """
                            SELECT COUNT(DISTINCT w.date) as workout_days,
                                   COUNT(s.id) as total_sets,
                                   AVG(s.weight) as avg_weight,
                                   SUM(s.weight * s.reps) as total_volume
                            FROM sets s
                            JOIN workouts w ON s.workout_id = w.id
                            WHERE w.date >= ?
                        """
                        cursor = conn.execute(query, (start_date,))
                    else:
                        query = """
                            SELECT COUNT(DISTINCT w.date) as workout_days,
                                   COUNT(s.id) as total_sets,
                                   AVG(s.weight) as avg_weight,
                                   SUM(s.weight * s.reps) as total_volume
                            FROM sets s
                            JOIN workouts w ON s.workout_id = w.id
                        """
                        cursor = conn.execute(query)
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        stats_data = [
                            ("トレーニング日数", f"{result[0]}日"),
                            ("総セット数", f"{result[1]}セット"),
                            ("平均重量", f"{result[2]:.1f}kg" if result[2] else "N/A"),
                            ("総ボリューム", f"{result[3]:.0f}kg" if result[3] else "N/A"),
                            ("平均セット数/日", f"{result[1]/result[0]:.1f}セット" if result[0] > 0 else "N/A"),
                        ]
            
            # テーブル更新
            self.stats_table.setRowCount(len(stats_data))
            
            for row, (item, value) in enumerate(stats_data):
                item_widget = QTableWidgetItem(item)
                item_widget.setFlags(item_widget.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.stats_table.setItem(row, 0, item_widget)
                
                value_widget = QTableWidgetItem(value)
                value_widget.setFlags(value_widget.flags() & ~Qt.ItemFlag.ItemIsEditable)
                value_widget.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.stats_table.setItem(row, 1, value_widget)
                
        except Exception as e:
            self.logger.error(f"Stats table update error: {e}")
    
    def refresh_data(self) -> None:
        """データ再読み込み（外部から呼び出し用）"""
        self.load_exercises()
        self.update_graph()