# ui/body_composition_goals_tab.py
"""体組成目標管理タブ"""

import logging
from datetime import date
from typing import List, Optional

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QWidget, QGroupBox, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QProgressBar, QDialog, QDialogButtonBox,
    QLineEdit, QDoubleSpinBox, QDateEdit, QTextEdit, QMessageBox,
    QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont, QPalette, QColor

from .base_tab import BaseTab


class BodyCompositionGoalDialog(QDialog):
    """体組成目標設定ダイアログ"""
    
    def __init__(self, db_manager, goal=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.goal = goal
        self.init_ui()
        
        if goal:
            self.setWindowTitle("体組成目標編集")
            self.load_goal_data()
        else:
            self.setWindowTitle("新しい体組成目標")
    
    def init_ui(self):
        """UI初期化"""
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("🎯 体組成目標設定" if not self.goal else "🎯 体組成目標編集")
        title_label.setFont(QFont("", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title_label)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 基本情報グループ
        basic_group = QGroupBox("📝 基本情報")
        basic_layout = QFormLayout()
        
        self.goal_name_edit = QLineEdit()
        self.goal_name_edit.setPlaceholderText("例: 夏までのボディメイク")
        basic_layout.addRow("目標名:", self.goal_name_edit)
        
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setDate(QDate.currentDate().addDays(90))
        self.target_date_edit.setCalendarPopup(True)
        basic_layout.addRow("目標達成日:", self.target_date_edit)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # 目標値グループ
        targets_group = QGroupBox("🎯 目標値")
        targets_layout = QFormLayout()
        
        # 体重目標
        weight_layout = QHBoxLayout()
        self.target_weight_check = QPushButton("☐ 体重目標")
        self.target_weight_check.setCheckable(True)
        self.target_weight_check.clicked.connect(self.toggle_weight_target)
        self.target_weight_spin = QDoubleSpinBox()
        self.target_weight_spin.setRange(30.0, 200.0)
        self.target_weight_spin.setSuffix(" kg")
        self.target_weight_spin.setDecimals(1)
        self.target_weight_spin.setEnabled(False)
        weight_layout.addWidget(self.target_weight_check)
        weight_layout.addWidget(self.target_weight_spin)
        targets_layout.addRow("", weight_layout)
        
        # 筋肉量目標
        muscle_layout = QHBoxLayout()
        self.target_muscle_check = QPushButton("☐ 筋肉量目標")
        self.target_muscle_check.setCheckable(True)
        self.target_muscle_check.clicked.connect(self.toggle_muscle_target)
        self.target_muscle_spin = QDoubleSpinBox()
        self.target_muscle_spin.setRange(20.0, 150.0)
        self.target_muscle_spin.setSuffix(" kg")
        self.target_muscle_spin.setDecimals(1)
        self.target_muscle_spin.setEnabled(False)
        muscle_layout.addWidget(self.target_muscle_check)
        muscle_layout.addWidget(self.target_muscle_spin)
        targets_layout.addRow("", muscle_layout)
        
        # 体脂肪率目標
        fat_layout = QHBoxLayout()
        self.target_fat_check = QPushButton("☐ 体脂肪率目標")
        self.target_fat_check.setCheckable(True)
        self.target_fat_check.clicked.connect(self.toggle_fat_target)
        self.target_fat_spin = QDoubleSpinBox()
        self.target_fat_spin.setRange(3.0, 50.0)
        self.target_fat_spin.setSuffix(" %")
        self.target_fat_spin.setDecimals(1)
        self.target_fat_spin.setEnabled(False)
        fat_layout.addWidget(self.target_fat_check)
        fat_layout.addWidget(self.target_fat_spin)
        targets_layout.addRow("", fat_layout)
        
        # BMI目標
        bmi_layout = QHBoxLayout()
        self.target_bmi_check = QPushButton("☐ BMI目標")
        self.target_bmi_check.setCheckable(True)
        self.target_bmi_check.clicked.connect(self.toggle_bmi_target)
        self.target_bmi_spin = QDoubleSpinBox()
        self.target_bmi_spin.setRange(15.0, 35.0)
        self.target_bmi_spin.setDecimals(1)
        self.target_bmi_spin.setEnabled(False)
        bmi_layout.addWidget(self.target_bmi_check)
        bmi_layout.addWidget(self.target_bmi_spin)
        targets_layout.addRow("", bmi_layout)
        
        targets_group.setLayout(targets_layout)
        scroll_layout.addWidget(targets_group)
        
        # 現在値グループ
        current_group = QGroupBox("📊 現在値（オプション）")
        current_layout = QFormLayout()
        
        self.current_weight_spin = QDoubleSpinBox()
        self.current_weight_spin.setRange(30.0, 200.0)
        self.current_weight_spin.setSuffix(" kg")
        self.current_weight_spin.setDecimals(1)
        self.current_weight_spin.setSpecialValueText("未設定")
        current_layout.addRow("現在体重:", self.current_weight_spin)
        
        self.current_muscle_spin = QDoubleSpinBox()
        self.current_muscle_spin.setRange(20.0, 150.0)
        self.current_muscle_spin.setSuffix(" kg")
        self.current_muscle_spin.setDecimals(1)
        self.current_muscle_spin.setSpecialValueText("未設定")
        current_layout.addRow("現在筋肉量:", self.current_muscle_spin)
        
        self.current_fat_spin = QDoubleSpinBox()
        self.current_fat_spin.setRange(3.0, 50.0)
        self.current_fat_spin.setSuffix(" %")
        self.current_fat_spin.setDecimals(1)
        self.current_fat_spin.setSpecialValueText("未設定")
        current_layout.addRow("現在体脂肪率:", self.current_fat_spin)
        
        current_group.setLayout(current_layout)
        scroll_layout.addWidget(current_group)
        
        # メモグループ
        notes_group = QGroupBox("📝 メモ")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("目標に関するメモを入力してください...")
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        scroll_layout.addWidget(notes_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # デフォルト値設定
        self.goal_name_edit.setText("夏までのボディメイク")
        self.target_weight_spin.setValue(75.0)
        self.target_muscle_spin.setValue(65.0)
        self.target_fat_spin.setValue(10.0)
        self.target_bmi_spin.setValue(22.0)
    
    def toggle_weight_target(self):
        """体重目標の有効/無効切り替え"""
        enabled = self.target_weight_check.isChecked()
        self.target_weight_spin.setEnabled(enabled)
        self.target_weight_check.setText("☑ 体重目標" if enabled else "☐ 体重目標")
    
    def toggle_muscle_target(self):
        """筋肉量目標の有効/無効切り替え"""
        enabled = self.target_muscle_check.isChecked()
        self.target_muscle_spin.setEnabled(enabled)
        self.target_muscle_check.setText("☑ 筋肉量目標" if enabled else "☐ 筋肉量目標")
    
    def toggle_fat_target(self):
        """体脂肪率目標の有効/無効切り替え"""
        enabled = self.target_fat_check.isChecked()
        self.target_fat_spin.setEnabled(enabled)
        self.target_fat_check.setText("☑ 体脂肪率目標" if enabled else "☐ 体脂肪率目標")
    
    def toggle_bmi_target(self):
        """BMI目標の有効/無効切り替え"""
        enabled = self.target_bmi_check.isChecked()
        self.target_bmi_spin.setEnabled(enabled)
        self.target_bmi_check.setText("☑ BMI目標" if enabled else "☐ BMI目標")
    
    def load_goal_data(self):
        """既存目標データの読み込み"""
        if not self.goal:
            return
        
        self.goal_name_edit.setText(self.goal.goal_name)
        
        # target_dateをQDateに変換
        target_date = self.goal.target_date
        if isinstance(target_date, str):
            from datetime import datetime
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        qdate = QDate(target_date.year, target_date.month, target_date.day)
        self.target_date_edit.setDate(qdate)
        
        # 目標値の設定
        if self.goal.target_weight:
            self.target_weight_check.setChecked(True)
            self.toggle_weight_target()
            self.target_weight_spin.setValue(self.goal.target_weight)
        
        if self.goal.target_muscle_mass:
            self.target_muscle_check.setChecked(True)
            self.toggle_muscle_target()
            self.target_muscle_spin.setValue(self.goal.target_muscle_mass)
        
        if self.goal.target_body_fat:
            self.target_fat_check.setChecked(True)
            self.toggle_fat_target()
            self.target_fat_spin.setValue(self.goal.target_body_fat)
        
        if self.goal.target_bmi:
            self.target_bmi_check.setChecked(True)
            self.toggle_bmi_target()
            self.target_bmi_spin.setValue(self.goal.target_bmi)
        
        # 現在値の設定
        if self.goal.current_weight:
            self.current_weight_spin.setValue(self.goal.current_weight)
        
        if self.goal.current_muscle_mass:
            self.current_muscle_spin.setValue(self.goal.current_muscle_mass)
        
        if self.goal.current_body_fat:
            self.current_fat_spin.setValue(self.goal.current_body_fat)
        
        if self.goal.notes:
            self.notes_edit.setText(self.goal.notes)
    
    def get_goal_data(self):
        """入力された目標データの取得"""
        from database.models import BodyCompositionGoal
        from datetime import date
        
        # 目標値の取得（チェックされている場合のみ）
        target_weight = self.target_weight_spin.value() if self.target_weight_check.isChecked() else None
        target_muscle = self.target_muscle_spin.value() if self.target_muscle_check.isChecked() else None
        target_fat = self.target_fat_spin.value() if self.target_fat_check.isChecked() else None
        target_bmi = self.target_bmi_spin.value() if self.target_bmi_check.isChecked() else None
        
        # 現在値の取得（0でない場合のみ）
        current_weight = self.current_weight_spin.value() if self.current_weight_spin.value() > 0 else None
        current_muscle = self.current_muscle_spin.value() if self.current_muscle_spin.value() > 0 else None
        current_fat = self.current_fat_spin.value() if self.current_fat_spin.value() > 0 else None
        
        # QDateをPython dateに変換
        qdate = self.target_date_edit.date()
        target_date = date(qdate.year(), qdate.month(), qdate.day())
        
        return BodyCompositionGoal(
            id=self.goal.id if self.goal else None,
            goal_name=self.goal_name_edit.text(),
            target_weight=target_weight,
            target_muscle_mass=target_muscle,
            target_body_fat=target_fat,
            target_bmi=target_bmi,
            target_date=target_date,
            current_weight=current_weight,
            current_muscle_mass=current_muscle,
            current_body_fat=current_fat,
            notes=self.notes_edit.toPlainText() or None,
            achieved=self.goal.achieved if self.goal else False
        )


class BodyCompositionGoalWidget(QFrame):
    """体組成目標表示ウィジェット"""
    
    editRequested = Signal(object)
    deleteRequested = Signal(object)
    achieveRequested = Signal(object)
    
    def __init__(self, goal, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.init_ui()
    
    def init_ui(self):
        """UI初期化"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                margin: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        # 目標名とステータス
        title_label = QLabel(f"🎯 {self.goal.goal_name}")
        title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # ステータスラベル
        status_label = QLabel(self.goal.get_status_text())
        status_label.setStyleSheet("color: #666; font-size: 10px;")
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # 総合進捗バー
        overall_progress = self.goal.overall_progress_percentage()
        overall_bar = QProgressBar()
        overall_bar.setValue(overall_progress)
        overall_bar.setFormat(f"総合進捗: {overall_progress}%")
        overall_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 2px;
            }
        """)
        layout.addWidget(overall_bar)
        
        # 詳細進捗
        details_layout = QGridLayout()
        row = 0
        
        if self.goal.target_weight:
            weight_progress = self.goal.weight_progress_percentage()
            details_layout.addWidget(QLabel("体重:"), row, 0)
            weight_bar = QProgressBar()
            weight_bar.setValue(weight_progress)
            weight_bar.setFormat(f"{weight_progress}%")
            weight_bar.setMaximumHeight(15)
            details_layout.addWidget(weight_bar, row, 1)
            
            current = self.goal.current_weight or 0
            target = self.goal.target_weight
            details_layout.addWidget(QLabel(f"{current:.1f}kg → {target:.1f}kg"), row, 2)
            row += 1
        
        if self.goal.target_muscle_mass:
            muscle_progress = self.goal.muscle_progress_percentage()
            details_layout.addWidget(QLabel("筋肉:"), row, 0)
            muscle_bar = QProgressBar()
            muscle_bar.setValue(muscle_progress)
            muscle_bar.setFormat(f"{muscle_progress}%")
            muscle_bar.setMaximumHeight(15)
            details_layout.addWidget(muscle_bar, row, 1)
            
            current = self.goal.current_muscle_mass or 0
            target = self.goal.target_muscle_mass
            details_layout.addWidget(QLabel(f"{current:.1f}kg → {target:.1f}kg"), row, 2)
            row += 1
        
        if self.goal.target_body_fat:
            fat_progress = self.goal.body_fat_progress_percentage()
            details_layout.addWidget(QLabel("体脂肪:"), row, 0)
            fat_bar = QProgressBar()
            fat_bar.setValue(fat_progress)
            fat_bar.setFormat(f"{fat_progress}%")
            fat_bar.setMaximumHeight(15)
            details_layout.addWidget(fat_bar, row, 1)
            
            current = self.goal.current_body_fat or 0
            target = self.goal.target_body_fat
            details_layout.addWidget(QLabel(f"{current:.1f}% → {target:.1f}%"), row, 2)
            row += 1
        
        layout.addLayout(details_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ 編集")
        edit_btn.clicked.connect(lambda: self.editRequested.emit(self.goal))
        button_layout.addWidget(edit_btn)
        
        if not self.goal.achieved:
            achieve_btn = QPushButton("✅ 達成")
            achieve_btn.clicked.connect(lambda: self.achieveRequested.emit(self.goal))
            button_layout.addWidget(achieve_btn)
        
        delete_btn = QPushButton("🗑️ 削除")
        delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self.goal))
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)


class BodyCompositionGoalsTab(BaseTab):
    """体組成目標管理タブ"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_goals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎯 体組成目標管理")
        title_label.setFont(QFont("", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # ボタン
        self.add_goal_btn = QPushButton("➕ 新しい目標")
        self.add_goal_btn.clicked.connect(self.add_goal)
        self.add_goal_btn.setStyleSheet("""
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
        header_layout.addWidget(self.add_goal_btn)
        
        self.update_progress_btn = QPushButton("🔄 進捗更新")
        self.update_progress_btn.clicked.connect(self.update_all_progress)
        header_layout.addWidget(self.update_progress_btn)
        
        layout.addLayout(header_layout)
        
        # サマリー
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(self.summary_label)
        
        # 目標リスト（スクロール可能）
        self.scroll_area = QScrollArea()
        self.goals_widget = QWidget()
        self.goals_layout = QVBoxLayout(self.goals_widget)
        self.goals_layout.addStretch()
        
        self.scroll_area.setWidget(self.goals_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        layout.addWidget(self.scroll_area)
    
    def load_goals(self):
        """目標データの読み込み"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.goals_layout.count() - 1)):
                item = self.goals_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
            
            # 目標を取得
            goals = self.db_manager.get_all_body_composition_goals()
            
            if not goals:
                no_goals_label = QLabel("目標が設定されていません。\n「➕ 新しい目標」ボタンから目標を作成してください。")
                no_goals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_goals_label.setStyleSheet("color: #999; font-size: 14px; padding: 50px;")
                self.goals_layout.insertWidget(0, no_goals_label)
            else:
                for goal in goals:
                    goal_widget = BodyCompositionGoalWidget(goal)
                    goal_widget.editRequested.connect(self.edit_goal)
                    goal_widget.deleteRequested.connect(self.delete_goal)
                    goal_widget.achieveRequested.connect(self.achieve_goal)
                    self.goals_layout.insertWidget(self.goals_layout.count() - 1, goal_widget)
            
            # サマリー更新
            self.update_summary()
            
        except Exception as e:
            self.logger.error(f"Failed to load goals: {e}")
            self.show_error("読み込みエラー", "目標の読み込みに失敗しました。")
    
    def update_summary(self):
        """サマリー更新"""
        try:
            summary = self.db_manager.get_body_composition_goals_summary()
            
            summary_text = (
                f"📊 目標総数: {summary['total']}個 | "
                f"✅ 達成: {summary['achieved']}個 | "
                f"🎯 アクティブ: {summary['active']}個 | "
                f"⏰ 期限切れ: {summary['overdue']}個 | "
                f"📈 達成率: {summary['achievement_rate']:.1f}%"
            )
            
            self.summary_label.setText(summary_text)
            
        except Exception as e:
            self.logger.error(f"Failed to update summary: {e}")
    
    def add_goal(self):
        """新しい目標の追加"""
        dialog = BodyCompositionGoalDialog(self.db_manager, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            goal_data = dialog.get_goal_data()
            
            if not goal_data.goal_name.strip():
                self.show_error("入力エラー", "目標名を入力してください。")
                return
            
            # 少なくとも1つの目標値が設定されているかチェック
            if not any([goal_data.target_weight, goal_data.target_muscle_mass, 
                       goal_data.target_body_fat, goal_data.target_bmi]):
                self.show_error("入力エラー", "少なくとも1つの目標値を設定してください。")
                return
            
            goal_id = self.db_manager.add_body_composition_goal(goal_data)
            
            if goal_id:
                self.show_info("目標追加", "🎉 新しい目標を追加しました！")
                self.load_goals()
            else:
                self.show_error("追加エラー", "目標の追加に失敗しました。")
    
    def edit_goal(self, goal):
        """目標の編集"""
        dialog = BodyCompositionGoalDialog(self.db_manager, goal, parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_goal = dialog.get_goal_data()
            
            if self.db_manager.update_body_composition_goal(updated_goal):
                self.show_info("目標更新", "✅ 目標を更新しました！")
                self.load_goals()
            else:
                self.show_error("更新エラー", "目標の更新に失敗しました。")
    
    def delete_goal(self, goal):
        """目標の削除"""
        reply = QMessageBox.question(
            self, "目標削除", 
            f"目標「{goal.goal_name}」を削除しますか？\n\nこの操作は元に戻せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_body_composition_goal(goal.id):
                self.show_info("目標削除", "🗑️ 目標を削除しました。")
                self.load_goals()
            else:
                self.show_error("削除エラー", "目標の削除に失敗しました。")
    
    def achieve_goal(self, goal):
        """目標の達成マーク"""
        reply = QMessageBox.question(
            self, "目標達成", 
            f"目標「{goal.goal_name}」を達成済みにマークしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.mark_body_composition_goal_as_achieved(goal.id):
                self.show_info("目標達成", "🎉 おめでとうございます！\n目標を達成済みにマークしました！")
                self.load_goals()
            else:
                self.show_error("更新エラー", "目標の更新に失敗しました。")
    
    def update_all_progress(self):
        """全目標の進捗を更新"""
        try:
            goals = self.db_manager.get_active_body_composition_goals()
            updated_count = 0
            
            for goal in goals:
                if self.db_manager.update_body_composition_goal_progress(goal.id):
                    updated_count += 1
            
            if updated_count > 0:
                self.show_info("進捗更新", f"📊 {updated_count}個の目標の進捗を更新しました！")
                self.load_goals()
            else:
                self.show_info("進捗更新", "更新する進捗データがありませんでした。\n体組成データを記録してから再度お試しください。")
                
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")
            self.show_error("更新エラー", "進捗の更新に失敗しました。")
    
    def refresh_data(self):
        """データの再読み込み（外部から呼び出し用）"""
        self.load_goals()