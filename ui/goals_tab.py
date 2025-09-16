# ui/goals_tab.py
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QLabel, QProgressBar, QWidget, QDialog,
                               QFormLayout, QComboBox, QDoubleSpinBox, QLineEdit,
                               QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

from .base_tab import BaseTab
from database.models import Goal

class GoalDialog(QDialog):
    """目標設定ダイアログ"""
    
    def __init__(self, db_manager, goal=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.goal = goal
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
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # フォームレイアウト
        form_layout = QFormLayout()
        
        # 種目選択
        self.exercise_combo = QComboBox()
        form_layout.addRow("種目:", self.exercise_combo)
        
        # 目標重量
        self.target_weight_spin = QDoubleSpinBox()
        self.target_weight_spin.setMinimum(0.0)
        self.target_weight_spin.setMaximum(500.0)
        self.target_weight_spin.setSingleStep(2.5)
        self.target_weight_spin.setDecimals(1)
        self.target_weight_spin.setSuffix(" kg")
        form_layout.addRow("目標重量:", self.target_weight_spin)
        
        # 現在重量
        self.current_weight_spin = QDoubleSpinBox()
        self.current_weight_spin.setMinimum(0.0)
        self.current_weight_spin.setMaximum(500.0)
        self.current_weight_spin.setSingleStep(2.5)
        self.current_weight_spin.setDecimals(1)
        self.current_weight_spin.setSuffix(" kg")
        form_layout.addRow("現在重量:", self.current_weight_spin)
        
        # 目標月
        self.target_month_edit = QLineEdit()
        self.target_month_edit.setPlaceholderText("YYYY-MM (例: 2024-12)")
        form_layout.addRow("目標月:", self.target_month_edit)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_exercises(self):
        """種目読み込み"""
        try:
            exercises = self.db_manager.get_all_exercises()
            self.exercise_combo.clear()
            
            for exercise in exercises:
                self.exercise_combo.addItem(exercise.display_name(), exercise.id)
                
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
    
    def __init__(self, goal, exercise_name, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.exercise_name = exercise_name
        self.init_ui()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # 種目名
        exercise_label = QLabel(self.exercise_name)
        exercise_label.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(exercise_label)
        
        # 目標情報
        target_info = f"目標: {self.goal.target_weight}kg（{self.goal.target_month}まで）"
        target_label = QLabel(target_info)
        layout.addWidget(target_label)
        
        # 現在の重量
        current_info = f"現在: {self.goal.current_weight}kg"
        current_label = QLabel(current_info)
        layout.addWidget(current_label)
        
        # 進捗バー
        progress = int((self.goal.current_weight / self.goal.target_weight) * 100) if self.goal.target_weight > 0 else 0
        progress = min(progress, 100)  # 100%を超えないように
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)
        layout.addWidget(self.progress_bar)
        
        # 進捗テキスト
        remaining = self.goal.target_weight - self.goal.current_weight
        if remaining > 0:
            progress_text = f"残り {remaining:.1f}kg ({progress}%)"
        else:
            progress_text = "目標達成！"
        
        progress_label = QLabel(progress_text)
        progress_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(progress_label)

class GoalsTab(BaseTab):
    """目標タブ"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_goals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title_label = QLabel("トレーニング目標")
        title_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; }")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 目標追加ボタン
        self.add_goal_button = QPushButton("目標追加")
        self.add_goal_button.clicked.connect(self.add_goal)
        header_layout.addWidget(self.add_goal_button)
        
        layout.addLayout(header_layout)
        
        # 目標リスト
        self.goals_list = QListWidget()
        self.goals_list.itemDoubleClicked.connect(self.edit_goal)
        layout.addWidget(self.goals_list)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self.edit_selected_goal)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_selected_goal)
        button_layout.addWidget(self.delete_button)
        
        self.achieve_button = QPushButton("達成済みにする")
        self.achieve_button.clicked.connect(self.mark_as_achieved)
        button_layout.addWidget(self.achieve_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # ボタン状態更新
        self.goals_list.itemSelectionChanged.connect(self.update_button_states)
        self.update_button_states()
    
    def load_goals(self):
        """目標読み込み"""
        try:
            # TODO: データベースから目標を読み込み
            # サンプルデータ
            sample_goals = [
                Goal(1, 1, 100.0, 85.0, "2024-12", False),
                Goal(2, 5, 80.0, 65.0, "2024-11", False),
                Goal(3, 10, 120.0, 120.0, "2024-10", True),
            ]
            
            # 種目名マッピング（サンプル）
            exercise_names = {
                1: "ベンチプレス（バーベル）",
                5: "ダンベルフライ（ダンベル）", 
                10: "デッドリフト（バーベル）"
            }
            
            self.goals_list.clear()
            
            for goal in sample_goals:
                exercise_name = exercise_names.get(goal.exercise_id, "未知の種目")
                goal_widget = GoalWidget(goal, exercise_name)
                
                list_item = QListWidgetItem()
                list_item.setSizeHint(goal_widget.sizeHint())
                list_item.setData(Qt.ItemDataRole.UserRole, goal)
                
                # 達成済みの場合は背景色を変更
                if goal.achieved:
                    goal_widget.setStyleSheet("QWidget { background-color: #E8F5E8; }")
                
                self.goals_list.addItem(list_item)
                self.goals_list.setItemWidget(list_item, goal_widget)
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "目標データの読み込みに失敗しました", str(e))
    
    def add_goal(self):
        """目標追加"""
        dialog = GoalDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            # TODO: データベースに保存
            self.show_info("目標追加", "目標を追加しました")
            self.load_goals()
    
    def edit_goal(self, item):
        """目標編集（ダブルクリック）"""
        self.edit_selected_goal()
    
    def edit_selected_goal(self):
        """選択された目標を編集"""
        current_item = self.goals_list.currentItem()
        if not current_item:
            return
        
        goal = current_item.data(Qt.ItemDataRole.UserRole)
        dialog = GoalDialog(self.db_manager, goal, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            # TODO: データベースを更新
            self.show_info("目標更新", "目標を更新しました")
            self.load_goals()
    
    def delete_selected_goal(self):
        """選択された目標を削除"""
        current_item = self.goals_list.currentItem()
        if not current_item:
            return
        
        goal = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "削除確認", 
                                   "選択した目標を削除しますか？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: データベースから削除
            self.show_info("目標削除", "目標を削除しました")
            self.load_goals()
    
    def mark_as_achieved(self):
        """達成済みにマーク"""
        current_item = self.goals_list.currentItem()
        if not current_item:
            return
        
        goal = current_item.data(Qt.ItemDataRole.UserRole)
        if goal.achieved:
            self.show_info("既に達成済み", "この目標は既に達成済みです")
            return
        
        reply = QMessageBox.question(self, "達成確認", 
                                   "この目標を達成済みにマークしますか？",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: データベースで達成フラグを更新
            self.show_info("目標達成", "おめでとうございます！目標を達成済みにマークしました")
            self.load_goals()
    
    def update_button_states(self):
        """ボタン状態更新"""
        has_selection = self.goals_list.currentItem() is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.achieve_button.setEnabled(has_selection)