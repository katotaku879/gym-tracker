# ui/body_stats_tab.py - 型エラー修正版
from typing import List, Dict, Optional, Any, Union
from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QComboBox, QLabel, 
                               QPushButton, QHeaderView, QSplitter,
                               QGroupBox, QFrame, QDialog, QMessageBox,
                               QWidget)
from PySide6.QtCore import Qt
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
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class BodyStatsTab(BaseTab):
    """体組成管理タブ - 型安全版"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_body_stats()
        self.update_summary()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("📊 体組成管理")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: #2c3e50; }")
        layout.addWidget(title_label)
        
        # サマリーエリア
        summary_frame = self.create_summary_area()
        layout.addWidget(summary_frame)
        
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
        self.setup_table()
        layout.addWidget(self.stats_table)
        
        return data_widget
    
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
        self.graph_type.currentTextChanged.connect(self.update_graph)
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
        self.period_combo.currentTextChanged.connect(self.update_graph)
        control_layout.addWidget(self.period_combo)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # グラフ
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 初期グラフ設定
        self.setup_initial_graph()
        
        return graph_widget
    
    def setup_table(self):
        """テーブル設定"""
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
        
        # テーブル設定
        self.stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setSortingEnabled(True)
        self.stats_table.itemSelectionChanged.connect(self.update_button_states)
        
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
    
    def setup_initial_graph(self):
        """初期グラフ設定"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '📊 体組成データを記録してグラフを表示してください',
                ha='center', va='center', transform=ax.transAxes,
                fontsize=14, color='#7f8c8d')
        self.canvas.draw()
    
    def load_body_stats(self):
        """体組成データ読み込み"""
        try:
            # TODO: データベースから体組成データを取得
            # サンプルデータ（実装時は削除）
            sample_data = [
                BodyStats(1, date(2024, 1, 1), 70.0, 15.0, 55.0),
                BodyStats(2, date(2024, 1, 8), 69.5, 14.8, 55.2),
                BodyStats(3, date(2024, 1, 15), 69.0, 14.5, 55.5),
            ]
            
            self.stats_table.setRowCount(len(sample_data))
            
            for row, stats in enumerate(sample_data):
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
                
                # BMI（仮の身長170cmで計算）
                if stats.weight:
                    bmi = stats.weight / (1.70 ** 2)
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
            
            # グラフ更新
            if MATPLOTLIB_AVAILABLE:
                self.update_graph()
            
        except Exception as e:
            self.show_error("データ読み込みエラー", "体組成データの読み込みに失敗しました", str(e))
    
    def update_summary(self):
        """サマリー更新"""
        try:
            # TODO: 実際のデータベースから取得
            # サンプルデータ
            self.current_weight_label.setText("⚖️ 体重: 69.0kg")
            self.current_body_fat_label.setText("📈 体脂肪率: 14.5%")
            self.current_muscle_label.setText("💪 筋肉量: 55.5kg")
            self.change_label.setText("📊 前月比: 体重: -1.0kg, 体脂肪率: -0.5%, 筋肉量: +0.5kg")
            
        except Exception as e:
            self.logger.error(f"Summary update failed: {e}")
    
    def update_graph(self):
        """グラフ更新（型安全版）"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        try:
            graph_type = self.graph_type.currentData()
            period_days = self.period_combo.currentData()
            
            # サンプルデータ（実装時は実際のデータに置換）
            stats_list = [
                BodyStats(1, date(2024, 1, 1), 70.0, 15.0, 55.0),
                BodyStats(2, date(2024, 1, 8), 69.5, 14.8, 55.2),
                BodyStats(3, date(2024, 1, 15), 69.0, 14.5, 55.5),
            ]
            
            if not stats_list:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, '📊 データがありません\n\n体組成データを記録してください',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=14, color='#95a5a6')
                self.canvas.draw()
                return
            
            # 日付とデータの準備（型安全）
            dates = []
            for stats in stats_list:
                if isinstance(stats.date, str):
                    dates.append(datetime.strptime(stats.date, '%Y-%m-%d'))
                else:
                    dates.append(datetime.combine(stats.date, datetime.min.time()))
            
            self.figure.clear()
            
            if graph_type == "weight":
                self.plot_weight_progress(dates, stats_list)
            elif graph_type == "body_fat":
                self.plot_body_fat_progress(dates, stats_list)
            elif graph_type == "muscle":
                self.plot_muscle_progress(dates, stats_list)
            elif graph_type == "all":
                self.plot_all_progress(dates, stats_list)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            self.logger.error(f"Graph update error: {e}")
            if MATPLOTLIB_AVAILABLE:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'❌ グラフの描画に失敗しました:\n{str(e)}',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='red')
                self.canvas.draw()
    
    def plot_weight_progress(self, dates: List[datetime], stats_list: List[BodyStats]):
        """体重推移グラフ（fill_between使用版）"""
        ax = self.figure.add_subplot(111)
        
        # 型安全なデータ抽出
        weights: List[float] = []
        weight_dates: List[datetime] = []
        
        for i, stats in enumerate(stats_list):
            if stats.weight is not None:
                weights.append(float(stats.weight))
                weight_dates.append(dates[i])
        
        if weight_dates and weights:
            ax.plot(weight_dates, weights, marker='o', linewidth=2, markersize=6,
                   color='#3498db', markerfacecolor='#2980b9', 
                   markeredgecolor='white', markeredgewidth=2)
            
            # matplotlib型定義の問題回避: fill_betweenは実際にはリストを受け取れる
            ax.fill_between(weight_dates, weights, alpha=0.3, color='#3498db')  # type: ignore[arg-type]
            
            ax.set_title('⚖️ 体重推移', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('体重 (kg)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        self.format_date_axis(ax, weight_dates)
    
    def plot_body_fat_progress(self, dates: List[datetime], stats_list: List[BodyStats]):
        """体脂肪率推移グラフ（型安全版）"""
        ax = self.figure.add_subplot(111)
        
        # 型安全なデータ抽出
        body_fats: List[float] = []
        body_fat_dates: List[datetime] = []
        
        for i, stats in enumerate(stats_list):
            if stats.body_fat_percentage is not None:
                body_fats.append(float(stats.body_fat_percentage))
                body_fat_dates.append(dates[i])
        
        if body_fat_dates and body_fats:
            ax.plot(body_fat_dates, body_fats, marker='s', linewidth=2, markersize=6,
                   color='#e74c3c', markerfacecolor='#c0392b', 
                   markeredgecolor='white', markeredgewidth=2)
            ax.fill_between(body_fat_dates, body_fats, alpha=0.3, color='#e74c3c')  # type: ignore[arg-type]
            
            ax.set_title('📈 体脂肪率推移', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('体脂肪率 (%)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        self.format_date_axis(ax, body_fat_dates)
    
    def plot_muscle_progress(self, dates: List[datetime], stats_list: List[BodyStats]):
        """筋肉量推移グラフ（型安全版）"""
        ax = self.figure.add_subplot(111)
        
        # 型安全なデータ抽出
        muscles: List[float] = []
        muscle_dates: List[datetime] = []
        
        for i, stats in enumerate(stats_list):
            if stats.muscle_mass is not None:
                muscles.append(float(stats.muscle_mass))
                muscle_dates.append(dates[i])
        
        if muscle_dates and muscles:
            ax.plot(muscle_dates, muscles, marker='^', linewidth=2, markersize=6,
                   color='#27ae60', markerfacecolor='#229954', 
                   markeredgecolor='white', markeredgewidth=2)
            ax.fill_between(muscle_dates, muscles, alpha=0.3, color='#27ae60')  # type: ignore[arg-type]
            
            ax.set_title('💪 筋肉量推移', fontsize=14, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('筋肉量 (kg)', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
        
        self.format_date_axis(ax, muscle_dates)
    
    def plot_all_progress(self, dates: List[datetime], stats_list: List[BodyStats]):
        """全項目推移グラフ（型安全版）"""
        ax1 = self.figure.add_subplot(111)
        
        # 体重データ（左軸）
        weights: List[float] = []
        weight_dates: List[datetime] = []
        
        for i, stats in enumerate(stats_list):
            if stats.weight is not None:
                weights.append(float(stats.weight))
                weight_dates.append(dates[i])
        
        if weight_dates and weights:
            ax1.plot(weight_dates, weights, marker='o', linewidth=2, 
                    color='#3498db', label='体重 (kg)')
            ax1.set_ylabel('体重 (kg)', fontsize=12, color='#3498db')
            ax1.tick_params(axis='y', labelcolor='#3498db')
        
        # 体脂肪率・筋肉量（右軸）
        ax2 = ax1.twinx()
        
        # 体脂肪率データ
        body_fats: List[float] = []
        body_fat_dates: List[datetime] = []
        
        for i, stats in enumerate(stats_list):
            if stats.body_fat_percentage is not None:
                body_fats.append(float(stats.body_fat_percentage))
                body_fat_dates.append(dates[i])
        
        # 筋肉量データ
        muscles: List[float] = []
        muscle_dates: List[datetime] = []
        
        for i, stats in enumerate(stats_list):
            if stats.muscle_mass is not None:
                muscles.append(float(stats.muscle_mass))
                muscle_dates.append(dates[i])
        
        lines1 = []
        lines2 = []
        
        if weight_dates:
            lines1 = ax1.get_lines()
        
        if body_fat_dates and body_fats:
            line2 = ax2.plot(body_fat_dates, body_fats, marker='s', linewidth=2,
                           color='#e74c3c', label='体脂肪率 (%)')
            lines2.extend(line2)
        
        if muscle_dates and muscles:
            line3 = ax2.plot(muscle_dates, muscles, marker='^', linewidth=2,
                           color='#27ae60', label='筋肉量 (kg)')
            lines2.extend(line3)
        
        ax2.set_ylabel('体脂肪率 (%) / 筋肉量 (kg)', fontsize=12)
        
        # 凡例
        labels1 = [l.get_label() for l in lines1]
        labels2 = [l.get_label() for l in lines2]
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        ax1.set_title('📊 体組成推移（全項目）', fontsize=14, fontweight='bold', color='#2c3e50')
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        all_dates = weight_dates if weight_dates else dates
        self.format_date_axis(ax1, all_dates)
    
    def format_date_axis(self, ax, dates: List[datetime]):
        """日付軸のフォーマット"""
        if not dates:
            return
            
        ax.set_xlabel('日付', fontsize=12)
        
        if len(dates) > 10:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def add_body_stats(self):
        """体組成データ追加"""
        # TODO: ダイアログ実装
        self.show_info("開発中", "体組成データ追加機能は実装中です")
    
    def edit_selected_stats(self):
        """選択された体組成データを編集"""
        # TODO: 編集機能実装
        self.show_info("開発中", "編集機能は実装中です")
    
    def delete_selected_stats(self):
        """選択された体組成データを削除"""
        # TODO: 削除機能実装
        reply = QMessageBox.question(self, "削除確認", "選択したデータを削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            self.show_info("開発中", "削除機能は実装中です")
    
    def update_button_states(self):
        """ボタン状態更新"""
        has_selection = self.stats_table.currentRow() >= 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def refresh_data(self):
        """データ再読み込み（外部から呼び出し用）"""
        self.load_body_stats()
        self.update_summary()