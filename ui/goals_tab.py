# ui/goals_tab.py - 完全版（データベース連携対応）
from typing import List, Dict, Optional
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QLabel, QProgressBar, QWidget, QDialog,
                               QFormLayout, QComboBox, QDoubleSpinBox, QLineEdit,
                               QDialogButtonBox, QMessageBox, QGroupBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .base_tab import BaseTab
from database.models import Goal

class GoalDialog(QDialog):
    """目標設定ダイアログ"""
    
    def __init__(self, db_manager, goal=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.goal = goal
        self.exercises = []
        self.init_ui()
        self.load_exercises()
        
        if goal:
            self.setWindowTitle("目標編集")
            self.load_goal_data()
        else:
            self.setWindowTitle("新規目標")
    
    def init_ui(self):
        """UI初期化"""
        self.setModal(True)
        self.resize(450, 350)
        
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("🎯 目標設定" if not self.goal else "🎯 目標編集")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # フォームレイアウト
        form_layout = QFormLayout()
        
        # 種目選択
        self.exercise_combo = QComboBox()
        self.exercise_combo.setMinimumWidth(200)
        form_layout.addRow("📋 種目:", self.exercise_combo)
        
        # 目標重量
        self.target_weight_spin = QDoubleSpinBox()
        self.target_weight_spin.setMinimum(0.0)
        self.target_weight_spin.setMaximum(500.0)
        self.target_weight_spin.setSingleStep(2.5)
        self.target_weight_spin.setDecimals(1)
        self.target_weight_spin.setSuffix(" kg")
        self.target_weight_spin.setMinimumWidth(120)
        form_layout.addRow("🎯 目標重量:", self.target_weight_spin)
        
        # 現在重量
        self.current_weight_spin = QDoubleSpinBox()
        self.current_weight_spin.setMinimum(0.0)
        self.current_weight_spin.setMaximum(500.0)
        self.current_weight_spin.setSingleStep(2.5)
        self.current_weight_spin.setDecimals(1)
        self.current_weight_spin.setSuffix(" kg")
        self.current_weight_spin.setMinimumWidth(120)
        form_layout.addRow("💪 現在重量:", self.current_weight_spin)
        
        # 目標月
        self.target_month_edit = QLineEdit()
        self.target_month_edit.setPlaceholderText("YYYY-MM (例: 2025-12)")
        self.target_month_edit.setMinimumWidth(150)
        form_layout.addRow("📅 目標月:", self.target_month_edit)
        
        # 記録から現在重量を更新ボタン
        self.update_current_button = QPushButton("📊 記録から現在重量を更新")
        self.update_current_button.clicked.connect(self.update_current_from_records)
        self.update_current_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        form_layout.addRow("", self.update_current_button)
        
        layout.addLayout(form_layout)
        
        # 説明文
        info_label = QLabel("💡 ヒント: 「記録から現在重量を更新」ボタンで、\nこれまでのトレーニング記録から最大1RMを自動設定できます。")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # ボタンのスタイル設定
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("💾 保存")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("❌ キャンセル")
        
        layout.addWidget(button_box)
    
    def load_exercises(self):
        """種目読み込み"""
        try:
            self.exercises = self.db_manager.get_all_exercises()
            self.exercise_combo.clear()
            
            if not self.exercises:
                self.exercise_combo.addItem("種目が見つかりません", None)
                return
            
            # カテゴリ別に整理
            categories = {}
            for exercise in self.exercises:
                if exercise.category not in categories:
                    categories[exercise.category] = []
                categories[exercise.category].append(exercise)
            
            # カテゴリ順で追加
            for category in ["胸", "背中", "脚", "肩", "腕"]:
                if category in categories:
                    for exercise in categories[category]:
                        display_name = f"[{exercise.category}] {exercise.name} ({exercise.variation})"
                        self.exercise_combo.addItem(display_name, exercise.id)
                        
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"種目データの読み込みに失敗しました: {e}")
    
    def load_goal_data(self):
        """目標データ読み込み"""
        if not self.goal:
            return
        
        # 種目選択
        for i in range(self.exercise_combo.count()):
            if self.exercise_combo.itemData(i) == self.goal.exercise_id:
                self.exercise_combo.setCurrentIndex(i)
                break
        
        self.target_weight_spin.setValue(self.goal.target_weight)
        self.current_weight_spin.setValue(self.goal.current_weight)
        self.target_month_edit.setText(self.goal.target_month)
    
    def update_current_from_records(self):
        """記録から現在重量を更新"""
        exercise_id = self.exercise_combo.currentData()
        if not exercise_id:
            QMessageBox.warning(self, "警告", "先に種目を選択してください。")
            return
        
        try:
            # その種目の最新の最大1RMを取得
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT MAX(s.one_rm)
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ? AND s.one_rm IS NOT NULL
                """, (exercise_id,))
                
                row = cursor.fetchone()
                if row and row[0]:
                    max_one_rm = float(row[0])
                    self.current_weight_spin.setValue(max_one_rm)
                    QMessageBox.information(self, "更新完了", 
                                          f"現在重量を {max_one_rm:.1f}kg に更新しました。\n"
                                          f"これまでの記録での最大1RMです。")
                else:
                    QMessageBox.information(self, "記録なし", 
                                          "選択した種目のトレーニング記録が見つかりません。\n"
                                          "手動で現在重量を入力してください。")
                    
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"記録の取得に失敗しました: {e}")
    
    def get_goal_data(self):
        """目標データ取得"""
        return Goal(
            id=self.goal.id if self.goal else None,
            exercise_id=self.exercise_combo.currentData(),
            target_weight=self.target_weight_spin.value(),
            current_weight=self.current_weight_spin.value(),
            target_month=self.target_month_edit.text(),
            achieved=self.goal.achieved if self.goal else False
        )

class GoalWidget(QWidget):
    """目標表示ウィジェット"""
    
    def __init__(self, goal_data: Dict, parent=None):
        super().__init__(parent)
        self.goal_data = goal_data
        self.goal = goal_data['goal']
        self.exercise_name = goal_data['exercise_name']
        self.init_ui()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 枠線設定
        self.setStyleSheet("""
            QWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                margin: 2px;
            }
        """)
        
        # 種目名と状態
        header_layout = QHBoxLayout()
        
        # 種目名
        exercise_label = QLabel(self.exercise_name)
        exercise_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; color: #2c3e50; border: none; }")
        header_layout.addWidget(exercise_label)
        
        header_layout.addStretch()
        
        # 達成状態
        if self.goal.achieved:
            status_label = QLabel("✅ 達成済み")
            status_label.setStyleSheet("QLabel { color: #27ae60; font-weight: bold; border: none; }")
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid #27ae60;
                    border-radius: 8px;
                    background-color: #e8f5e8;
                    margin: 2px;
                }
            """)
        else:
            # 達成可能かチェック
            if self.goal.current_weight >= self.goal.target_weight:
                status_label = QLabel("🎯 達成可能！")
                status_label.setStyleSheet("QLabel { color: #f39c12; font-weight: bold; border: none; }")
            else:
                status_label = QLabel("💪 挑戦中")
                status_label.setStyleSheet("QLabel { color: #3498db; font-weight: bold; border: none; }")
        
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # 目標情報
        target_info = f"🎯 目標: {self.goal.target_weight:.1f}kg（{self.goal.target_month}まで）"
        target_label = QLabel(target_info)
        target_label.setStyleSheet("QLabel { color: #34495e; border: none; }")
        layout.addWidget(target_label)
        
        # 現在の重量
        current_info = f"💪 現在: {self.goal.current_weight:.1f}kg"
        current_label = QLabel(current_info)
        current_label.setStyleSheet("QLabel { color: #7f8c8d; border: none; }")
        layout.addWidget(current_label)
        
        # 進捗バー
        if self.goal.target_weight > 0:
            progress = int((self.goal.current_weight / self.goal.target_weight) * 100)
            progress = min(progress, 100)  # 100%を超えないように
        else:
            progress = 0
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)
        
        # 進捗バーのスタイル
        if progress >= 100:
            color = "#27ae60"  # 緑
        elif progress >= 75:
            color = "#f39c12"  # オレンジ
        else:
            color = "#3498db"  # 青
            
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
        
        layout.addWidget(self.progress_bar)
        
        # 進捗テキスト
        remaining = self.goal.target_weight - self.goal.current_weight
        if remaining > 0:
            if self.goal.achieved:
                progress_text = f"🎉 目標達成！ ({progress}%)"
            else:
                progress_text = f"残り {remaining:.1f}kg ({progress}%)"
        else:
            progress_text = "🎉 目標達成！"
        
        progress_label = QLabel(progress_text)
        progress_label.setStyleSheet("QLabel { color: #7f8c8d; font-size: 12px; border: none; }")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(progress_label)

class GoalsTab(BaseTab):
    """目標タブ - データベース連携版"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_goals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎯 トレーニング目標")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: #2c3e50; }")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 目標追加ボタン
        self.add_goal_button = QPushButton("➕ 目標追加")
        self.add_goal_button.clicked.connect(self.add_goal)
        self.add_goal_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        header_layout.addWidget(self.add_goal_button)
        
        layout.addLayout(header_layout)
        
        # 達成可能な目標の通知エリア
        self.notification_frame = QFrame()
        self.notification_frame.setVisible(False)
        self.notification_layout = QVBoxLayout(self.notification_frame)
        layout.addWidget(self.notification_frame)
        
        # 目標リスト
        self.goals_list = QListWidget()
        self.goals_list.itemDoubleClicked.connect(self.edit_goal)
        self.goals_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                border: none;
                padding: 5px;
            }
        """)
        layout.addWidget(self.goals_list)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("✏️ 編集")
        self.edit_button.clicked.connect(self.edit_selected_goal)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("🗑️ 削除")
        self.delete_button.clicked.connect(self.delete_selected_goal)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.delete_button)
        
        self.achieve_button = QPushButton("🏆 達成済みにする")
        self.achieve_button.clicked.connect(self.mark_as_achieved)
        self.achieve_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.achieve_button)
        
        self.update_all_button = QPushButton("📊 全目標の現在重量を更新")
        self.update_all_button.clicked.connect(self.update_all_current_weights)
        self.update_all_button.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        button_layout.addWidget(self.update_all_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # ボタン状態更新
        self.goals_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()
    
    def load_goals(self):
        """目標読み込み"""
        try:
            goal_data_list = self.db_manager.get_all_goals_with_exercise_names()
            
            self.goals_list.clear()
            
            if not goal_data_list:
                # 目標がない場合のメッセージ
                empty_item = QListWidgetItem()
                empty_widget = QLabel("📝 まだ目標が設定されていません。\n「目標追加」ボタンから新しい目標を設定しましょう！")
                empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_widget.setStyleSheet("""
                    QLabel {
                        color: #7f8c8d;
                        font-size: 14px;
                        padding: 40px;
                        background-color: white;
                        border: 2px dashed #bdc3c7;
                        border-radius: 8px;
                        margin: 10px;
                    }
                """)
                empty_item.setSizeHint(empty_widget.sizeHint())
                self.goals_list.addItem(empty_item)
                self.goals_list.setItemWidget(empty_item, empty_widget)
                
                # 通知エリアを非表示
                self.notification_frame.setVisible(False)
                return
            
            # 達成可能な目標をチェック
            achievable_goals = [goal_data for goal_data in goal_data_list 
                              if not goal_data['goal'].achieved and 
                              goal_data['goal'].current_weight >= goal_data['goal'].target_weight]
            
            # 達成可能な目標の通知表示
            self.show_achievable_goals_notification(achievable_goals)
            
            for goal_data in goal_data_list:
                goal_widget = GoalWidget(goal_data)
                
                list_item = QListWidgetItem()
                list_item.setSizeHint(goal_widget.sizeHint())
                list_item.setData(Qt.ItemDataRole.UserRole, goal_data)
                
                self.goals_list.addItem(list_item)
                self.goals_list.setItemWidget(list_item, goal_widget)
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "目標データの読み込みに失敗しました", str(e))
    
    def show_achievable_goals_notification(self, achievable_goals: List[Dict]):
        """達成可能な目標の通知表示"""
        # 既存の通知をクリア
        for i in reversed(range(self.notification_layout.count())):
            child = self.notification_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not achievable_goals:
            self.notification_frame.setVisible(False)
            return
        
        # 通知ウィジェット作成
        notification_widget = QGroupBox("🎉 目標達成可能な種目があります！")
        notification_widget.setStyleSheet("""
            QGroupBox {
                background-color: #fff3cd;
                border: 2px solid #f39c12;
                border-radius: 8px;
                font-weight: bold;
                color: #856404;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)
        
        notification_layout = QVBoxLayout(notification_widget)
        
        for goal_data in achievable_goals[:3]:  # 最大3個まで表示
            goal = goal_data['goal']
            exercise_name = goal_data['exercise_name']
            
            text = f"🎯 {exercise_name}: {goal.current_weight:.1f}kg → {goal.target_weight:.1f}kg"
            label = QLabel(text)
            label.setStyleSheet("QLabel { color: #856404; font-weight: normal; }")
            notification_layout.addWidget(label)
        
        if len(achievable_goals) > 3:
            more_label = QLabel(f"他{len(achievable_goals) - 3}件の目標も達成可能です。")
            more_label.setStyleSheet("QLabel { color: #856404; font-style: italic; }")
            notification_layout.addWidget(more_label)
        
        self.notification_layout.addWidget(notification_widget)
        self.notification_frame.setVisible(True)
    
    def add_goal(self):
        """目標追加"""
        dialog = GoalDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            
            # 入力値検証
            if not goal_data.exercise_id:
                self.show_warning("入力エラー", "種目を選択してください。")
                return
            
            if goal_data.target_weight <= 0:
                self.show_warning("入力エラー", "目標重量は0より大きい値を入力してください。")
                return
            
            if not goal_data.target_month.strip():
                self.show_warning("入力エラー", "目標月を入力してください。")
                return
            
            # データベースに保存
            goal_id = self.db_manager.add_goal(goal_data)
            if goal_id:
                self.show_info("目標追加", "✅ 新しい目標を追加しました！\n頑張って達成しましょう 💪")
                self.load_goals()
            else:
                self.show_error("保存エラー", "目標の保存に失敗しました。")
    
    def edit_goal(self, item):
        """目標編集（ダブルクリック）"""
        self.edit_selected_goal()
    
    def edit_selected_goal(self):
        """選択された目標を編集"""
        current_item = self.goals_list.currentItem()
        if not current_item:
            return
        
        goal_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not goal_data:
            return
        
        dialog = GoalDialog(self.db_manager, goal_data['goal'], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_goal = dialog.get_goal_data()
            
            # データベースを更新
            if self.db_manager.update_goal(updated_goal):
                self.show_info("目標更新", "✅ 目標を更新しました！")
                self.load_goals()
            else:
                self.show_error("更新エラー", "目標の更新に失敗しました。")
    
    def delete_selected_goal(self):
        """選択された目標を削除"""
        current_item = self.goals_list.currentItem()
        if not current_item:
            return
        
        goal_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not goal_data:
            return
        
        goal = goal_data['goal']
        exercise_name = goal_data['exercise_name']
        
        reply = QMessageBox.question(self, "🗑️ 削除確認", 
                                   f"以下の目標を削除しますか？\n\n"
                                   f"種目: {exercise_name}\n"
                                   f"目標: {goal.target_weight:.1f}kg\n"
                                   f"期限: {goal.target_month}\n\n"
                                   f"⚠️ この操作は取り消せません。",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_goal(goal.id):
                self.show_info("目標削除", "🗑️ 目標を削除しました。")
                self.load_goals()
            else:
                self.show_error("削除エラー", "目標の削除に失敗しました。")
    
    def mark_as_achieved(self):
        """達成済みにマーク"""
        current_item = self.goals_list.currentItem()
        if not current_item:
            return
        
        goal_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not goal_data:
            return
        
        goal = goal_data['goal']
        exercise_name = goal_data['exercise_name']
        
        if goal.achieved:
            self.show_info("既に達成済み", "🏆 この目標は既に達成済みです！")
            return
        
        reply = QMessageBox.question(self, "🏆 達成確認", 
                                   f"以下の目標を達成済みにマークしますか？\n\n"
                                   f"種目: {exercise_name}\n"
                                   f"目標: {goal.target_weight:.1f}kg\n\n"
                                   f"🎉 おめでとうございます！",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.Yes)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.mark_goal_as_achieved(goal.id):
                self.show_info("目標達成", "🎉 おめでとうございます！\n目標を達成済みにマークしました 🏆")
                self.load_goals()
            else:
                self.show_error("更新エラー", "目標の更新に失敗しました。")
    
    def update_all_current_weights(self):
        """全目標の現在重量を記録から更新"""
        try:
            goal_data_list = self.db_manager.get_all_goals_with_exercise_names()
            
            if not goal_data_list:
                self.show_info("更新対象なし", "更新する目標がありません。")
                return
            
            updated_count = 0
            for goal_data in goal_data_list:
                goal = goal_data['goal']
                if not goal.achieved:  # 未達成の目標のみ更新
                    if self.db_manager.update_goal_current_weight_from_records(goal.id):
                        updated_count += 1
            
            if updated_count > 0:
                self.show_info("更新完了", f"📊 {updated_count}個の目標の現在重量を\nトレーニング記録から更新しました！")
                self.load_goals()
            else:
                self.show_info("更新なし", "更新対象となる記録が見つかりませんでした。")
                
        except Exception as e:
            self.show_error("更新エラー", "現在重量の更新に失敗しました", str(e))
    
    def update_button_states(self):
        """ボタン状態更新"""
        current_item = self.goals_list.currentItem()
        has_selection = current_item is not None
        
        # 空のリストの場合は無効化
        if self.goals_list.count() == 1:
            first_item = self.goals_list.item(0)
            if first_item and not first_item.data(Qt.ItemDataRole.UserRole):
                has_selection = False
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.achieve_button.setEnabled(has_selection)
        
        # 達成済みの目標の場合は達成ボタンを無効化
        if has_selection and current_item.data(Qt.ItemDataRole.UserRole):
            goal_data = current_item.data(Qt.ItemDataRole.UserRole)
            if goal_data and goal_data['goal'].achieved:
                self.achieve_button.setEnabled(False)
    
    def refresh_data(self):
        """データ再読み込み（外部から呼び出し用）"""
        self.load_goals()