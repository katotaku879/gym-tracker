# ui/goal_dialog_v2.py
"""
3セット×重量×回数方式の目標設定ダイアログ
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QLineEdit, QTextEdit, QLabel, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from database.models import Goal

class GoalDialogV2(QDialog):
    """3セット方式対応の目標設定ダイアログ"""
    
    def __init__(self, db_manager, goal=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.goal = goal  # 編集時は既存の目標
        self.setWindowTitle("🎯 トレーニング目標設定（3セット方式）")
        self.setMinimumSize(500, 600)
        
        self.init_ui()
        self.load_exercises()
        if self.goal:
            self.load_goal_data()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("🏋️‍♂️ 3セット×重量×回数 目標設定")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 種目選択
        exercise_group = QGroupBox("🎯 対象種目")
        exercise_layout = QVBoxLayout()
        
        self.exercise_combo = QComboBox()
        self.exercise_combo.setMinimumHeight(40)
        exercise_layout.addWidget(self.exercise_combo)
        
        exercise_group.setLayout(exercise_layout)
        layout.addWidget(exercise_group)
        
        # 目標設定
        target_group = QGroupBox("📊 目標設定")
        target_layout = QFormLayout()
        
        # 目標重量
        weight_layout = QHBoxLayout()
        self.target_weight_spin = QDoubleSpinBox()
        self.target_weight_spin.setMinimum(0.0)
        self.target_weight_spin.setMaximum(500.0)
        self.target_weight_spin.setSingleStep(2.5)
        self.target_weight_spin.setDecimals(1)
        self.target_weight_spin.setSuffix(" kg")
        self.target_weight_spin.setMinimumWidth(120)
        
        # よく使われる重量のクイック設定ボタン
        quick_weights = [60, 70, 80, 90, 100]
        for weight in quick_weights:
            btn = QPushButton(f"{weight}")
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, w=weight: self.target_weight_spin.setValue(w))
            weight_layout.addWidget(btn)
        
        weight_layout.insertWidget(0, self.target_weight_spin)
        target_layout.addRow("🏋️‍♀️ 目標重量:", weight_layout)
        
        # 目標回数
        reps_layout = QHBoxLayout()
        self.target_reps_spin = QSpinBox()
        self.target_reps_spin.setMinimum(1)
        self.target_reps_spin.setMaximum(50)
        self.target_reps_spin.setValue(8)
        self.target_reps_spin.setSuffix(" 回")
        self.target_reps_spin.setMinimumWidth(100)
        
        # よく使われる回数のクイック設定
        quick_reps = [5, 8, 10, 12]
        for reps in quick_reps:
            btn = QPushButton(f"{reps}")
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, r=reps: self.target_reps_spin.setValue(r))
            reps_layout.addWidget(btn)
        
        reps_layout.insertWidget(0, self.target_reps_spin)
        target_layout.addRow("🔢 目標回数:", reps_layout)
        
        # 目標セット数
        sets_layout = QHBoxLayout()
        self.target_sets_spin = QSpinBox()
        self.target_sets_spin.setMinimum(1)
        self.target_sets_spin.setMaximum(10)
        self.target_sets_spin.setValue(3)
        self.target_sets_spin.setSuffix(" セット")
        self.target_sets_spin.setMinimumWidth(100)
        
        # セット数のクイック設定
        quick_sets = [3, 4, 5]
        for sets in quick_sets:
            btn = QPushButton(f"{sets}")
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, s=sets: self.target_sets_spin.setValue(s))
            sets_layout.addWidget(btn)
        
        sets_layout.insertWidget(0, self.target_sets_spin)
        target_layout.addRow("📚 目標セット数:", sets_layout)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 目標プレビュー
        preview_group = QGroupBox("👀 目標プレビュー")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        # プレビュー更新用の接続
        self.target_weight_spin.valueChanged.connect(self.update_preview)
        self.target_reps_spin.valueChanged.connect(self.update_preview)
        self.target_sets_spin.valueChanged.connect(self.update_preview)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # その他の設定
        other_group = QGroupBox("⚙️ その他の設定")
        other_layout = QFormLayout()
        
        # 目標期限
        self.target_month_edit = QLineEdit()
        self.target_month_edit.setPlaceholderText("YYYY-MM (例: 2025-12)")
        other_layout.addRow("📅 目標期限:", self.target_month_edit)
        
        # メモ
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("目標に関するメモ...")
        other_layout.addRow("📝 メモ:", self.notes_edit)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        # 現在の進捗（編集時のみ表示）
        if self.goal:
            progress_group = QGroupBox("📈 現在の進捗")
            progress_layout = QFormLayout()
            
            self.current_sets_spin = QSpinBox()
            self.current_sets_spin.setMinimum(0)
            self.current_sets_spin.setMaximum(10)
            self.current_sets_spin.setSuffix(" セット")
            progress_layout.addRow("✅ 達成済みセット数:", self.current_sets_spin)
            
            self.update_progress_btn = QPushButton("🔄 記録から自動更新")
            self.update_progress_btn.clicked.connect(self.update_progress_from_records)
            progress_layout.addRow("", self.update_progress_btn)
            
            progress_group.setLayout(progress_layout)
            layout.addWidget(progress_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.cancel_btn = QPushButton("❌ キャンセル")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 初期プレビュー更新
        self.update_preview()
    
    def load_exercises(self):
        """種目読み込み"""
        try:
            exercises = self.db_manager.get_all_exercises()
            self.exercise_combo.clear()
            self.exercise_combo.addItem("種目を選択してください", None)
            
            # カテゴリ別にグループ化
            categories = {}
            for exercise in exercises:
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
            print(f"種目データの読み込みに失敗: {e}")
    
    def update_preview(self):
        """プレビュー更新"""
        weight = self.target_weight_spin.value()
        reps = self.target_reps_spin.value()
        sets = self.target_sets_spin.value()
        
        preview_text = f"🎯 目標: {weight}kg × {reps}回 × {sets}セット\n"
        preview_text += f"💪 達成条件: {weight}kg以上で{reps}回以上を{sets}セット完遂"
        
        self.preview_label.setText(preview_text)
    
    def update_progress_from_records(self):
        """記録から進捗を自動更新"""
        exercise_id = self.exercise_combo.currentData()
        if not exercise_id or not self.goal:
            return
        
        # 最新記録から達成セット数を計算
        if self.db_manager.update_goal_progress_from_workouts(self.goal.id):
            # 更新された情報を再読み込み
            updated_goal = self.db_manager.get_goal(self.goal.id)
            if updated_goal:
                self.current_sets_spin.setValue(updated_goal.current_achieved_sets)
    
    def load_goal_data(self):
        """既存目標データの読み込み"""
        if not self.goal:
            return
        
        # 種目選択
        for i in range(self.exercise_combo.count()):
            if self.exercise_combo.itemData(i) == self.goal.exercise_id:
                self.exercise_combo.setCurrentIndex(i)
                break
        
        self.target_weight_spin.setValue(self.goal.target_weight)
        self.target_reps_spin.setValue(getattr(self.goal, 'target_reps', 8))
        self.target_sets_spin.setValue(getattr(self.goal, 'target_sets', 3))
        self.target_month_edit.setText(self.goal.target_month)
        
        if hasattr(self.goal, 'notes') and self.goal.notes:
            self.notes_edit.setText(self.goal.notes)
        
        if hasattr(self, 'current_sets_spin'):
            self.current_sets_spin.setValue(getattr(self.goal, 'current_achieved_sets', 0))
    
    def get_goal_data(self):
        """目標データ取得"""
        return Goal(
            id=self.goal.id if self.goal else None,
            exercise_id=self.exercise_combo.currentData(),
            target_weight=self.target_weight_spin.value(),
            target_reps=self.target_reps_spin.value(),
            target_sets=self.target_sets_spin.value(),
            current_achieved_sets=self.current_sets_spin.value() if hasattr(self, 'current_sets_spin') else 0,
            current_max_weight=0.0,  # 後で記録から更新
            target_month=self.target_month_edit.text(),
            achieved=False,
            notes=self.notes_edit.toPlainText() or None
        )