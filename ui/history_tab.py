# ui/history_tab.py
from typing import List, Any, Optional
from datetime import date, datetime
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidget, 
                               QTableWidgetItem, QComboBox, QLineEdit, 
                               QDateEdit, QPushButton, QLabel, QHeaderView,
                               QMessageBox)
from PySide6.QtCore import Qt, QDate

from .base_tab import BaseTab

class HistoryTab(BaseTab):
    """履歴タブ"""
    
    def __init__(self, db_manager) -> None:
        super().__init__(db_manager)
        self.current_page: int = 0
        self.page_size: int = 50
        self.filtered_data: List[Any] = []  # フィルタ後のデータ
        self.apply_current_filter: bool = False
        self.init_ui()
        self.load_exercises()
        self.load_history()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("トレーニング履歴")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; margin-bottom: 10px; }")
        layout.addWidget(title_label)
        
        # フィルタエリア
        filter_frame = self.create_filter_area()
        layout.addWidget(filter_frame)
        
        # 履歴テーブル
        self.history_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.history_table)
        
        # ページネーションエリア
        pagination_layout = self.create_pagination_area()
        layout.addLayout(pagination_layout)
    
    def create_filter_area(self):
        """フィルタエリア作成"""
        from PySide6.QtWidgets import QGroupBox
        
        filter_group = QGroupBox("フィルタ")
        filter_layout = QVBoxLayout(filter_group)
        
        # 1行目: 日付フィルタ
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("期間:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("〜"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        date_layout.addStretch()
        filter_layout.addLayout(date_layout)
        
        # 2行目: 種目・検索フィルタ
        filter_layout2 = QHBoxLayout()
        
        filter_layout2.addWidget(QLabel("種目:"))
        self.exercise_filter = QComboBox()
        self.exercise_filter.setMinimumWidth(200)
        filter_layout2.addWidget(self.exercise_filter)
        
        filter_layout2.addWidget(QLabel("検索:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("種目名で検索...")
        self.search_box.setMinimumWidth(150)
        filter_layout2.addWidget(self.search_box)
        
        # フィルタボタン
        self.filter_button = QPushButton("フィルタ適用")
        self.filter_button.clicked.connect(self.apply_filter)
        self.filter_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        filter_layout2.addWidget(self.filter_button)
        
        self.clear_filter_button = QPushButton("クリア")
        self.clear_filter_button.clicked.connect(self.clear_filter)
        filter_layout2.addWidget(self.clear_filter_button)
        
        filter_layout2.addStretch()
        filter_layout.addLayout(filter_layout2)
        
        return filter_group
    
    def create_pagination_area(self):
        """ページネーションエリア作成"""
        pagination_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("◀ 前のページ")
        self.prev_button.clicked.connect(self.previous_page)
        pagination_layout.addWidget(self.prev_button)
        
        self.page_label = QLabel("ページ: 1 / 1")
        self.page_label.setStyleSheet("QLabel { margin: 0 15px; }")
        pagination_layout.addWidget(self.page_label)
        
        self.next_button = QPushButton("次のページ ▶")
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)
        
        pagination_layout.addStretch()
        
        # 統計情報
        self.record_count_label = QLabel("総レコード数: 0")
        self.record_count_label.setStyleSheet("QLabel { color: #666; }")
        pagination_layout.addWidget(self.record_count_label)
        
        return pagination_layout
    
    def setup_table(self):
        """テーブル設定"""
        columns = ["日付", "種目", "セット", "重量", "回数", "1RM", "操作"]
        self.history_table.setColumnCount(len(columns))
        self.history_table.setHorizontalHeaderLabels(columns)
        
        # 列幅設定
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 日付
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)            # 種目
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # セット
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 重量
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 回数
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 1RM
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 操作
        
        # テーブル設定
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSortingEnabled(True)
        
        # ヘッダースタイル
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def load_exercises(self):
        """種目読み込み"""
        try:
            exercises = self.db_manager.get_all_exercises()
            self.exercise_filter.clear()
            self.exercise_filter.addItem("全ての種目", None)
            
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
                        self.exercise_filter.addItem(exercise.display_name(), exercise.id)
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "種目データの読み込みに失敗しました", str(e))
    
    def load_history(self) -> None:
        """履歴読み込み（フィルタ対応版）"""
        try:
            # フィルタ条件を取得
            if hasattr(self, 'apply_current_filter') and self.apply_current_filter:
                # QDateからPythonのdateオブジェクトに安全に変換
                try:
                    start_date_py = self.start_date.date().toPython()
                    end_date_py = self.end_date.date().toPython()
                    
                    # 型安全な変換（isinstance チェック追加）
                    if hasattr(start_date_py, 'year') and isinstance(start_date_py, date):
                        start_date_filtered = start_date_py
                    else:
                        start_date_filtered = date.today()
                        
                    if hasattr(end_date_py, 'year') and isinstance(end_date_py, date):
                        end_date_filtered = end_date_py
                    else:
                        end_date_filtered = date.today()
                        
                except Exception as date_error:
                    self.logger.warning(f"Date conversion error: {date_error}")
                    start_date_filtered = date.today()
                    end_date_filtered = date.today()
                
                # 選択された種目のIDを取得
                selected_exercise_id = self.exercise_filter.currentData()
                if self.exercise_filter.currentText() == "全ての種目":
                    selected_exercise_id = None
                
                # フィルタ付きでデータ取得
                offset = self.current_page * self.page_size
                history_data = self.db_manager.get_history_filtered(
                    start_date=start_date_filtered,
                    end_date=end_date_filtered,
                    exercise_id=selected_exercise_id,
                    page_size=self.page_size,
                    offset=offset
                )
                
                # フィルタ後の総レコード数
                filtered_total = self.db_manager.get_filtered_record_count(
                    start_date=start_date_filtered,
                    end_date=end_date_filtered,
                    exercise_id=selected_exercise_id
                )
                
                # 検索フィルタを追加適用
                search_text = self.search_box.text().lower().strip()
                if search_text:
                    history_data = [
                        record for record in history_data
                        if search_text in f"{record[1]} {record[2]}".lower()
                    ]
                
                # 総レコード数
                total_records = self.db_manager.get_total_record_count()
                self.record_count_label.setText(f"表示中: {len(history_data)}件 / フィルタ結果: {filtered_total}件 / 総レコード数: {total_records}件")
                
                # ページネーション計算（フィルタ結果基準）
                total_pages = max(1, (filtered_total + self.page_size - 1) // self.page_size)
                
            else:
                # フィルタなしの通常表示
                total_records = self.db_manager.get_total_record_count()
                
                if total_records == 0:
                    self.record_count_label.setText("総レコード数: 0 (データがありません)")
                    self.history_table.setRowCount(0)
                    self.update_pagination_buttons(0, 0)
                    return
                
                offset = self.current_page * self.page_size
                history_data = self.db_manager.get_history_paginated(self.page_size, offset)
                
                self.record_count_label.setText(f"総レコード数: {total_records}件")
                total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
            
            # ページ表示更新
            current_page_display = self.current_page + 1
            self.page_label.setText(f"ページ: {current_page_display} / {total_pages}")
            
            # ボタン状態更新
            self.update_pagination_buttons(len(history_data), total_pages)
            
            # テーブル更新
            self.update_table(history_data)
            
        except Exception as e:
            self.show_error("データ読み込みエラー", "履歴データの読み込みに失敗しました", str(e))
    
    def update_pagination_buttons(self, current_records: int, total_pages: int) -> None:
        """ページネーションボタン状態更新"""
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)
        
        # ボタンテキストの更新
        if self.current_page > 0:
            self.prev_button.setText("◀ 前のページ")
        else:
            self.prev_button.setText("◀ 前のページ (無効)")
            
        if self.current_page < total_pages - 1:
            self.next_button.setText("次のページ ▶")
        else:
            self.next_button.setText("次のページ ▶ (無効)")
    
    def update_table(self, data: List[Any]) -> None:
        """テーブル更新"""
        self.history_table.setRowCount(len(data))
        
        for row, record in enumerate(data):
            try:
                # 日付
                date_item = QTableWidgetItem(str(record[0]))
                date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.history_table.setItem(row, 0, date_item)
                
                # 種目
                exercise_name = f"{record[1]}（{record[2]}）"
                exercise_item = QTableWidgetItem(exercise_name)
                exercise_item.setFlags(exercise_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.history_table.setItem(row, 1, exercise_item)
                
                # セット番号
                set_item = QTableWidgetItem(str(record[3]))
                set_item.setFlags(set_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                set_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.history_table.setItem(row, 2, set_item)
                
                # 重量
                weight_value = float(record[4]) if record[4] is not None else 0.0
                weight_item = QTableWidgetItem(f"{weight_value:.1f} kg")
                weight_item.setFlags(weight_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                weight_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.history_table.setItem(row, 3, weight_item)
                
                # 回数
                reps_value = int(record[5]) if record[5] is not None else 0
                reps_item = QTableWidgetItem(f"{reps_value} 回")
                reps_item.setFlags(reps_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                reps_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.history_table.setItem(row, 4, reps_item)
                
                # 1RM
                one_rm_value = float(record[6]) if record[6] is not None else 0.0
                one_rm_item = QTableWidgetItem(f"{one_rm_value:.1f} kg")
                one_rm_item.setFlags(one_rm_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                one_rm_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.history_table.setItem(row, 5, one_rm_item)
                
                # 操作ボタン（将来の機能用）
                action_item = QTableWidgetItem("編集")
                action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.history_table.setItem(row, 6, action_item)
                
            except (ValueError, TypeError, IndexError) as e:
                self.logger.error(f"Error updating table row {row}: {e}")
                continue
    
    def apply_filter(self) -> None:
        """フィルタ適用"""
        self.apply_current_filter = True
        self.current_page = 0  # フィルタ適用時はページをリセット
        self.load_history()
    
    def filter_data(self, data: List[Any]) -> List[Any]:
        """データフィルタリング（完全版）"""
        filtered = []
        
        # フィルタ条件を取得（型安全な方法）
        try:
            start_date_qdate = self.start_date.date().toPython()
            end_date_qdate = self.end_date.date().toPython()
            
            # 安全な型変換
            if hasattr(start_date_qdate, 'year') and isinstance(start_date_qdate, date):
                start_date_obj = start_date_qdate
            else:
                start_date_obj = date.today()
                
            if hasattr(end_date_qdate, 'year') and isinstance(end_date_qdate, date):
                end_date_obj = end_date_qdate
            else:
                end_date_obj = date.today()
                
        except Exception as e:
            self.logger.warning(f"Date conversion error: {e}")
            start_date_obj = date.today()
            end_date_obj = date.today()
        
        selected_exercise_name = self.exercise_filter.currentText()
        search_text = self.search_box.text().lower().strip()
        
        for record in data:
            try:
                # 1. 日付フィルタ
                record_date_obj = self._parse_record_date(record[0])
                if record_date_obj is None or not isinstance(record_date_obj, date):
                    continue  # 日付パースエラーまたは型不一致の場合はスキップ
                
                # 型が確定した後で比較（すべてdateオブジェクト）
                if record_date_obj < start_date_obj or record_date_obj > end_date_obj:
                    continue
                
                # 2. 種目フィルタ
                if selected_exercise_name != "全ての種目":
                    current_exercise_name = f"{record[1]}（{record[2]}）"
                    if selected_exercise_name != current_exercise_name:
                        continue
                
                # 3. 検索フィルタ
                if search_text:
                    exercise_full_name = f"{record[1]} {record[2]}".lower()
                    if search_text not in exercise_full_name:
                        continue
                
                # 全条件をパスした場合のみ追加
                filtered.append(record)
                
            except (IndexError, AttributeError, TypeError) as e:
                self.logger.warning(f"Filter error for record {record}: {e}")
                continue
        
        return filtered
    
    def _parse_record_date(self, date_value: Any) -> Optional[date]:
        """レコードの日付を安全にパース"""
        try:
            if isinstance(date_value, date):
                return date_value
            elif isinstance(date_value, str):
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            elif hasattr(date_value, 'date') and callable(getattr(date_value, 'date')):
                # datetime オブジェクトの場合
                return date_value.date()
            else:
                # 最後の手段として文字列変換してパース
                date_str = str(date_value)
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.warning(f"Date parsing failed for value {date_value}: {e}")
            return None
    
    def clear_filter(self) -> None:
        """フィルタクリア"""
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        self.exercise_filter.setCurrentIndex(0)
        self.search_box.clear()
        self.apply_current_filter = False
        self.current_page = 0
        self.load_history()
    
    def previous_page(self) -> None:
        """前のページ"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_history()
    
    def next_page(self) -> None:
        """次のページ"""
        total_records = self.db_manager.get_total_record_count()
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_history()
    
    def refresh_data(self) -> None:
        """データ再読み込み（外部から呼び出し用）"""
        self.current_page = 0
        self.load_history()