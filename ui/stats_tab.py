# ui/stats_tab.py - 完全版（既存ファイルを置き換え）
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.cm as cm
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
                               QTableWidget, QTableWidgetItem, QSplitter,
                               QHeaderView, QWidget, QGroupBox, QScrollArea,
                               QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .base_tab import BaseTab

# matplotlib日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']


class StatsTab(BaseTab):
    """統計タブ - 完全版"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_exercises()
        self.setup_graph()
        self.update_stats_summary()
    
    def init_ui(self) -> None:
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("📊 トレーニング統計 & 分析")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }")
        layout.addWidget(title_label)
        
        # コントロール区域
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
        splitter.setSizes([700, 350])
        
        layout.addWidget(splitter)
    
    def create_control_area(self) -> QGroupBox:
        """コントロールエリア作成"""
        control_group = QGroupBox("📈 グラフ設定")
        control_layout = QVBoxLayout(control_group)
        
        # 1行目: グラフ種類と種目
        row1_layout = QHBoxLayout()
        
        # グラフ種類選択
        row1_layout.addWidget(QLabel("グラフ種類:"))
        self.graph_type = QComboBox()
        self.graph_type.addItem("💪 1RM推移", "one_rm_progress")
        self.graph_type.addItem("⚖️ 重量推移", "weight_progress")  
        self.graph_type.addItem("📊 ボリューム推移", "volume_progress")
        self.graph_type.addItem("📅 頻度分析", "frequency_analysis")
        self.graph_type.addItem("🎯 部位別分析", "category_analysis")
        self.graph_type.currentTextChanged.connect(self.update_graph)
        row1_layout.addWidget(self.graph_type)

        row1_layout.addStretch()
        control_layout.addLayout(row1_layout)

        # 【追加】2行目: 部位と種目選択
        row2_layout = QHBoxLayout()
        
        # 部位選択
        row2_layout.addWidget(QLabel("部位:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("すべての部位", "all")
        self.category_combo.addItem("胸", "胸")
        self.category_combo.addItem("背中", "背中")
        self.category_combo.addItem("脚", "脚")
        self.category_combo.addItem("肩", "肩")
        self.category_combo.addItem("腕", "腕")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        row2_layout.addWidget(self.category_combo)
        
        # 種目選択
        row2_layout.addWidget(QLabel("種目:"))
        self.exercise_combo = QComboBox()
        self.exercise_combo.currentTextChanged.connect(self.update_graph)
        row2_layout.addWidget(self.exercise_combo)
        
        # 更新ボタン
        refresh_btn = QPushButton("🔄 更新")
        refresh_btn.clicked.connect(self.refresh_data)
        row1_layout.addWidget(refresh_btn)
        
        row2_layout.addStretch()
        control_layout.addLayout(row2_layout)
        
        # 【修正】3行目: 期間選択 (既存の2行目を3行目に)
        row3_layout = QHBoxLayout()
        
        row3_layout.addWidget(QLabel("期間:"))
        self.period_combo = QComboBox()
        self.period_combo.addItem("過去1ヶ月", 30)
        self.period_combo.addItem("過去3ヶ月", 90)
        self.period_combo.addItem("過去6ヶ月", 180)
        self.period_combo.addItem("過去1年", 365)
        self.period_combo.addItem("全期間", -1)
        self.period_combo.setCurrentIndex(2)  # デフォルトは過去6ヶ月
        self.period_combo.currentTextChanged.connect(self.update_graph)
        row3_layout.addWidget(self.period_combo)
        
        row3_layout.addStretch()
        control_layout.addLayout(row3_layout)  # row2_layout → row3_layout
        
        return control_group
    
    def create_graph_area(self) -> QWidget:
        """グラフエリア作成"""
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        graph_layout.addWidget(self.canvas)
        
        return graph_widget
    
    def create_stats_area(self) -> QWidget:
        """統計エリア作成"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # ベスト記録セクション
        best_records_title = QLabel("🏆 ベスト記録")
        best_records_title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; color: #e74c3c; }")
        stats_layout.addWidget(best_records_title)
        
        self.best_records_table = QTableWidget()
        self.setup_best_records_table()
        stats_layout.addWidget(self.best_records_table)
        
        # 統計サマリーセクション
        stats_title = QLabel("📊 統計サマリー")
        stats_title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; color: #3498db; margin-top: 10px; }")
        stats_layout.addWidget(stats_title)
        
        self.stats_table = QTableWidget()
        self.setup_stats_table()
        stats_layout.addWidget(self.stats_table)
        
        return stats_widget
    
    def setup_best_records_table(self) -> None:
        """ベスト記録テーブル設定"""
        columns = ["種目", "最大重量", "最大回数", "最大1RM"]
        self.best_records_table.setColumnCount(len(columns))
        self.best_records_table.setHorizontalHeaderLabels(columns)
        
        # 列幅設定
        header = self.best_records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.best_records_table.setAlternatingRowColors(True)
        self.best_records_table.setMaximumHeight(200)
        
        # ヘッダースタイル
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #e74c3c;
                color: white;
                padding: 6px;
                border: 1px solid #c0392b;
                font-weight: bold;
            }
        """)
    
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
                background-color: #3498db;
                color: white;
                padding: 6px;
                border: 1px solid #2980b9;
                font-weight: bold;
            }
        """)
    
    def load_exercises(self) -> None:
        """種目読み込み"""
        try:
            exercises = self.db_manager.get_all_exercises()
            self.exercises = exercises  # 👈 追加
            
            # 最初はすべての種目を表示
            self.update_exercise_combo("all")  # 👈 この1行で置き換え
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "種目データの読み込みに失敗しました", str(e))
    
    def on_category_changed(self) -> None:
        """部位選択変更時の処理"""
        selected_category = self.category_combo.currentData()
        self.update_exercise_combo(selected_category)
        self.update_graph()

    def on_graph_type_changed(self) -> None:
        """グラフタイプ変更時の処理"""
        graph_type = self.graph_type.currentData()
        
        # 頻度分析と部位別分析では種目選択を無効化
        if graph_type in ["frequency_analysis", "category_analysis"]:
            self.category_combo.setEnabled(False)
            self.exercise_combo.setEnabled(False)
        else:
            self.category_combo.setEnabled(True)
            self.exercise_combo.setEnabled(True)
        
        self.update_graph()

    def update_exercise_combo(self, category: str) -> None:
        """種目コンボボックス更新"""
        self.exercise_combo.clear()
        
        if category == "all":
            self.exercise_combo.addItem("種目を選択してください", None)
            
            # カテゴリ別に整理して追加
            categories = {}
            for exercise in self.exercises:
                if exercise.category not in categories:
                    categories[exercise.category] = []
                categories[exercise.category].append(exercise)
            
            # カテゴリ順で追加
            for cat in ["胸", "背中", "脚", "肩", "腕"]:
                if cat in categories:
                    for exercise in categories[cat]:
                        display_name = f"[{exercise.category}] {exercise.name} ({exercise.variation})"
                        self.exercise_combo.addItem(display_name, exercise.id)
        else:
            # 選択された部位の種目のみ表示
            self.exercise_combo.addItem("種目を選択してください", None)
            filtered_exercises = [ex for ex in self.exercises if ex.category == category]
            
            for exercise in filtered_exercises:
                display_name = f"{exercise.name} ({exercise.variation})"
                self.exercise_combo.addItem(display_name, exercise.id)

    def update_best_records(self) -> None:
        """ベスト記録更新"""
        try:
            best_records = self.get_best_records()
            self.best_records_table.setRowCount(len(best_records))
            
            for row, record in enumerate(best_records):
                # 種目名
                exercise_item = QTableWidgetItem(record['exercise_name'])
                exercise_item.setFlags(exercise_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.best_records_table.setItem(row, 0, exercise_item)
                
                # 最大重量
                weight_item = QTableWidgetItem(f"{record['max_weight']:.1f}kg")
                weight_item.setFlags(weight_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                weight_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.best_records_table.setItem(row, 1, weight_item)
                
                # 最大回数
                reps_item = QTableWidgetItem(f"{record['max_reps']}回")
                reps_item.setFlags(reps_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                reps_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.best_records_table.setItem(row, 2, reps_item)
                
                # 最大1RM
                one_rm_item = QTableWidgetItem(f"{record['max_one_rm']:.1f}kg")
                one_rm_item.setFlags(one_rm_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                one_rm_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.best_records_table.setItem(row, 3, one_rm_item)
                
        except Exception as e:
            self.logger.error(f"Best records update failed: {e}")
    
    def get_best_records(self) -> List[Dict]:
        """ベスト記録取得"""
        try:
            with self.db_manager.get_connection() as conn:
                query = """
                SELECT 
                    e.name || '（' || e.variation || '）' as exercise_name,
                    MAX(s.weight) as max_weight,
                    MAX(s.reps) as max_reps,
                    MAX(s.one_rm) as max_one_rm
                FROM sets s
                JOIN exercises e ON s.exercise_id = e.id
                GROUP BY s.exercise_id
                HAVING COUNT(s.id) > 0
                ORDER BY max_one_rm DESC
                LIMIT 10
                """
                cursor = conn.execute(query)
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get best records: {e}")
            return []
    
    def update_stats_summary(self) -> None:
        """統計サマリー更新"""
        try:
            stats = self.get_workout_statistics()
            
            stats_data = [
                ("📝 総ワークアウト数", f"{stats['total_workouts']}回"),
                ("🏋️ 総セット数", f"{stats['total_sets']}セット"),
                ("📈 平均セット数/日", f"{stats['avg_sets_per_workout']:.1f}"),
                ("🔥 連続トレーニング日数", f"{stats['current_streak']}日"),
                ("⭐ 最長連続日数", f"{stats['max_streak']}日"),
                ("📅 今月のトレーニング日数", f"{stats['this_month_workouts']}日"),
                ("⚖️ 平均重量", f"{stats['avg_weight']:.1f}kg"),
                ("📊 総重量", f"{stats['total_volume']:.0f}kg"),
            ]
            
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
            self.logger.error(f"Stats summary update failed: {e}")
    
    def get_workout_statistics(self) -> Dict[str, float]:
        """ワークアウト統計取得"""
        try:
            with self.db_manager.get_connection() as conn:
                stats = {}
                
                # 総ワークアウト数
                cursor = conn.execute("SELECT COUNT(DISTINCT id) FROM workouts")
                result = cursor.fetchone()
                stats['total_workouts'] = result[0] if result else 0
                
                # 総セット数
                cursor = conn.execute("SELECT COUNT(*) FROM sets")
                result = cursor.fetchone()
                stats['total_sets'] = result[0] if result else 0
                
                # 平均セット数/ワークアウト
                if stats['total_workouts'] > 0:
                    stats['avg_sets_per_workout'] = stats['total_sets'] / stats['total_workouts']
                else:
                    stats['avg_sets_per_workout'] = 0
                
                # 連続トレーニング日数計算
                stats['current_streak'] = self.calculate_current_streak(conn)
                stats['max_streak'] = self.calculate_max_streak(conn)
                
                # 今月のトレーニング日数
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT date) 
                    FROM workouts 
                    WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                """)
                result = cursor.fetchone()
                stats['this_month_workouts'] = result[0] if result else 0
                
                # 平均重量
                cursor = conn.execute("SELECT AVG(weight) FROM sets WHERE weight > 0")
                result = cursor.fetchone()
                stats['avg_weight'] = result[0] if result and result[0] else 0
                
                # 総重量（重量×回数）
                cursor = conn.execute("SELECT SUM(weight * reps) FROM sets")
                result = cursor.fetchone()
                stats['total_volume'] = result[0] if result and result[0] else 0
                
                return stats
        except Exception as e:
            self.logger.error(f"Workout statistics fetch failed: {e}")
            return {
                'total_workouts': 0, 'total_sets': 0, 'avg_sets_per_workout': 0,
                'current_streak': 0, 'max_streak': 0, 'this_month_workouts': 0,
                'avg_weight': 0, 'total_volume': 0
            }
    
    def calculate_current_streak(self, conn) -> int:
        """現在の連続トレーニング日数計算"""
        try:
            cursor = conn.execute("""
                SELECT DISTINCT date 
                FROM workouts 
                ORDER BY date DESC
                LIMIT 30
            """)
            dates = [row[0] for row in cursor.fetchall()]
            
            if not dates:
                return 0
            
            today = date.today()
            streak = 0
            current_date = today
            
            for date_str in dates:
                workout_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                if workout_date == current_date or workout_date == current_date - timedelta(days=1):
                    streak += 1
                    current_date = workout_date - timedelta(days=1)
                else:
                    break
            
            return streak
        except Exception as e:
            self.logger.error(f"Current streak calculation failed: {e}")
            return 0
    
    def calculate_max_streak(self, conn) -> int:
        """最長連続日数計算"""
        try:
            cursor = conn.execute("""
                SELECT DISTINCT date 
                FROM workouts 
                ORDER BY date
            """)
            dates = [row[0] for row in cursor.fetchall()]
            
            if not dates:
                return 0
            
            max_streak = 1
            current_streak = 1
            
            for i in range(1, len(dates)):
                prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d').date()
                curr_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
                
                if curr_date == prev_date + timedelta(days=1):
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            
            return max_streak
        except Exception as e:
            self.logger.error(f"Max streak calculation failed: {e}")
            return 0
    
    def setup_graph(self) -> None:
        """グラフ初期設定"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '📊 種目を選択してグラフを表示してください',
                ha='center', va='center', transform=ax.transAxes, 
                fontsize=16, color='#7f8c8d')
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
                        ax.text(0.5, 0.5, '💪 種目を選択して1RM推移を確認してください',
                                ha='center', va='center', transform=ax.transAxes,
                                fontsize=14, color='#e74c3c')
                    else:
                        self.plot_one_rm_progress(ax, exercise_id, period_days)
                elif graph_type == "weight_progress":
                    if exercise_id is None:
                        ax.text(0.5, 0.5, '⚖️ 種目を選択して重量推移を確認してください',
                                ha='center', va='center', transform=ax.transAxes,
                                fontsize=14, color='#e74c3c')
                    else:
                        self.plot_weight_progress(ax, exercise_id, period_days)
                elif graph_type == "volume_progress":
                    if exercise_id is None:
                        ax.text(0.5, 0.5, '📊 種目を選択してボリューム推移を確認してください',
                                ha='center', va='center', transform=ax.transAxes,
                                fontsize=14, color='#e74c3c')
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
                ax.text(0.5, 0.5, f'❌ グラフの描画に失敗しました:\n{str(plot_error)}',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='red')
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
            ax.text(0.5, 0.5, '📊 データがありません\n\nトレーニング記録を追加してください',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='#95a5a6')
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
            # グラデーション効果
            ax.plot(dates, one_rms, marker='o', linewidth=3, markersize=8, 
                   color='#e74c3c', markerfacecolor='#c0392b', markeredgecolor='white', markeredgewidth=2)
            ax.fill_between(dates, one_rms, alpha=0.3, color='#e74c3c')
            
            ax.set_title('💪 1RM推移 - 成長トラッキング', fontsize=16, fontweight='bold', color='#2c3e50')
            ax.set_xlabel('日付', fontsize=12)
            ax.set_ylabel('1RM (kg)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # 最高記録にアノテーション
            max_idx = one_rms.index(max(one_rms))
            max_date = dates[max_idx]
            max_value = one_rms[max_idx]
            ax.annotate(f'🏆 最高記録\n{max_value:.1f}kg',
                       xy=(max_date, max_value),
                       xytext=(20, 20), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2'))
            
            # 日付フォーマット
            if len(dates) > 10:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_weight_progress(self, ax, exercise_id: int, period_days: int) -> None:
        """重量推移グラフ"""
        data = self.get_exercise_data(exercise_id, period_days)
        
        if not data:
            ax.text(0.5, 0.5, '📊 データがありません\n\nトレーニング記録を追加してください',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='#95a5a6')
            return
        
        # 日付ごとの最大重量と平均重量を計算
        daily_weights = {}
        for row in data:
            workout_date = datetime.strptime(str(row[0]), '%Y-%m-%d').date()
            weight = float(row[1])
            
            if workout_date not in daily_weights:
                daily_weights[workout_date] = []
            daily_weights[workout_date].append(weight)
        
        # データをソートして描画
        dates = sorted(daily_weights.keys())
        max_weights = [max(daily_weights[d]) for d in dates]
        avg_weights = [sum(daily_weights[d])/len(daily_weights[d]) for d in dates]
        
        if dates:
            ax.plot(dates, max_weights, marker='o', linewidth=3, markersize=8, 
                   label='最大重量', color='#3498db', markerfacecolor='#2980b9', 
                   markeredgecolor='white', markeredgewidth=2)
            ax.plot(dates, avg_weights, marker='s', linewidth=2, markersize=6, 
                   label='平均重量', color='#95a5a6', alpha=0.8)
            
            ax.set_title('⚖️ 重量推移 - パフォーマンス分析', fontsize=16, fontweight='bold', color='#2c3e50')
            ax.set_xlabel('日付', fontsize=12)
            ax.set_ylabel('重量 (kg)', fontsize=12)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # 日付フォーマット
            if len(dates) > 10:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def plot_volume_progress(self, ax, exercise_id: int, period_days: int) -> None:
        """ボリューム推移グラフ"""
        data = self.get_exercise_data(exercise_id, period_days)
        
        if not data:
            ax.text(0.5, 0.5, '📊 データがありません\n\nトレーニング記録を追加してください',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='#95a5a6')
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
            colors = cm.viridis(np.linspace(0, 1, len(volumes)))  # type: ignore
            bars = ax.bar(dates, volumes, width=1, alpha=0.8, color=colors)
            
            ax.set_title('📊 トレーニングボリューム推移', fontsize=16, fontweight='bold', color='#2c3e50')
            ax.set_xlabel('日付', fontsize=12)
            ax.set_ylabel('ボリューム (kg)', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y', linestyle='--')
            
            # 最高ボリュームにアノテーション
            max_idx = volumes.index(max(volumes))
            max_date = dates[max_idx]
            max_volume = volumes[max_idx]
            ax.annotate(f'📈 最高ボリューム\n{max_volume:.0f}kg',
                       xy=(max_date, max_volume),
                       xytext=(20, 20), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2'))
            
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
                    bars = ax.bar(categories, frequencies, color=colors[:len(categories)], alpha=0.8)
                    
                    ax.set_title('📅 部位別トレーニング頻度', fontsize=16, fontweight='bold', color='#2c3e50')
                    ax.set_xlabel('筋肉部位', fontsize=12)
                    ax.set_ylabel('トレーニング日数', fontsize=12)
                    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
                    
                    # 棒グラフに値を表示
                    for bar, freq in zip(bars, frequencies):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                               f'{freq}日', ha='center', va='bottom', fontweight='bold')
                else:
                    ax.text(0.5, 0.5, '📊 データがありません\n\nトレーニング記録を追加してください',
                            ha='center', va='center', transform=ax.transAxes,
                            fontsize=14, color='#95a5a6')
                    
        except Exception as e:
            self.logger.error(f"Frequency analysis error: {e}")
            ax.text(0.5, 0.5, '❌ データの取得に失敗しました',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='red')
    
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
                    categories = [f"{row[0]}\n({row[1]}セット)" for row in results]
                    set_counts = [row[1] for row in results]
                    
                    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98']
                    
                    wedges, texts, autotexts = ax.pie(set_counts, labels=categories, 
                                                     autopct='%1.1f%%', startangle=90,
                                                     colors=colors[:len(categories)],
                                                     explode=[0.05] * len(categories))
                    
                    ax.set_title('🎯 部位別セット数の割合', fontsize=16, fontweight='bold', color='#2c3e50')
                    
                    # テキストのフォントサイズ調整
                    for text in texts:
                        text.set_fontsize(10)
                        text.set_fontweight('bold')
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                        autotext.set_fontsize(10)
                else:
                    ax.text(0.5, 0.5, '📊 データがありません\n\nトレーニング記録を追加してください',
                            ha='center', va='center', transform=ax.transAxes,
                            fontsize=14, color='#95a5a6')
                    
        except Exception as e:
            self.logger.error(f"Category analysis error: {e}")
            ax.text(0.5, 0.5, '❌ データの取得に失敗しました',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14, color='red')
    
    def update_stats_table(self, graph_type: str, exercise_id: Optional[int], period_days: int) -> None:
        """統計テーブル更新（グラフ種別に応じて）"""
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
                        ("📊 総セット数", f"{len(data)}セット"),
                        ("⚖️ 最大重量", f"{max(weights):.1f}kg"),
                        ("📈 平均重量", f"{sum(weights)/len(weights):.1f}kg"),
                        ("💪 最大1RM", f"{max(one_rms):.1f}kg" if one_rms else "N/A"),
                        ("📊 総ボリューム", f"{sum(volumes):.0f}kg"),
                        ("📈 平均ボリューム/セット", f"{sum(volumes)/len(volumes):.1f}kg"),
                    ]
            else:
                # 全体統計
                stats = self.get_workout_statistics()
                stats_data = [
                    ("📝 総ワークアウト数", f"{stats['total_workouts']}回"),
                    ("🏋️ 総セット数", f"{stats['total_sets']}セット"),
                    ("📈 平均セット数/日", f"{stats['avg_sets_per_workout']:.1f}"),
                    ("🔥 連続トレーニング日数", f"{stats['current_streak']}日"),
                    ("⭐ 最長連続日数", f"{stats['max_streak']}日"),
                    ("📅 今月のトレーニング日数", f"{stats['this_month_workouts']}日"),
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
        try:
            self.load_exercises()
            self.update_best_records()
            self.update_stats_summary()
            self.update_graph()
            QMessageBox.information(self, "更新完了", "📊 統計データを更新しました！")
        except Exception as e:
            self.logger.error(f"Data refresh failed: {e}")
            self.show_error("更新エラー", "データの更新に失敗しました", str(e))