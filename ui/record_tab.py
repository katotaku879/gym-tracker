# ui/record_tab.py
from datetime import date
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
                               QPushButton, QScrollArea, QWidget, QFrame,
                               QDoubleSpinBox, QSpinBox, QMessageBox, QDateEdit)
from PySide6.QtCore import Qt, QDate

from .base_tab import BaseTab
from database.models import Set, Workout
from utils.validation import validate_set_data
from utils.constants import (WEIGHT_MIN, WEIGHT_MAX, WEIGHT_STEP, REPS_MIN, REPS_MAX, 
                            EXERCISE_CATEGORIES)

class SetWidget(QWidget):
    """セット入力ウィジェット"""
    
    def __init__(self, set_number: int):
        super().__init__()
        self.set_number = set_number
        self.init_ui()
    
    def init_ui(self):
        """UI初期化"""
        layout = QHBoxLayout(self)
        
        # セット番号ラベル
        set_label = QLabel(f"セット#{self.set_number}")
        set_label.setMinimumWidth(80)
        layout.addWidget(set_label)
        
        # 重量入力
        layout.addWidget(QLabel("重量:"))
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setMinimum(WEIGHT_MIN)
        self.weight_spin.setMaximum(WEIGHT_MAX)
        self.weight_spin.setSingleStep(WEIGHT_STEP)
        self.weight_spin.setDecimals(1)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setMinimumWidth(100)
        layout.addWidget(self.weight_spin)
        
        # 回数入力
        layout.addWidget(QLabel("回数:"))
        self.reps_spin = QSpinBox()
        self.reps_spin.setMinimum(REPS_MIN)
        self.reps_spin.setMaximum(REPS_MAX)
        self.reps_spin.setSuffix(" 回")
        self.reps_spin.setMinimumWidth(80)
        layout.addWidget(self.reps_spin)
        
        # 削除ボタン
        self.delete_button = QPushButton("削除")
        self.delete_button.setMaximumWidth(60)
        layout.addWidget(self.delete_button)
        
        layout.addStretch()
    
    def get_set_data(self) -> dict:
        """セットデータ取得"""
        return {
            'weight': self.weight_spin.value(),
            'reps': self.reps_spin.value()
        }
    
    def set_previous_data(self, weight: float, reps: int):
        """前回データ設定"""
        self.weight_spin.setValue(weight)
        self.reps_spin.setValue(reps)

class RecordTab(BaseTab):
    """記録タブ"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.current_exercise_id = None
        self.set_widgets = []
        self.exercises_by_category = {}  # カテゴリ別種目データ
        self.init_ui()
        self.load_exercises()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # 日付選択
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("日付:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # 部位選択
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("部位:"))
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        layout.addLayout(category_layout)
        
        # 種目選択
        exercise_layout = QHBoxLayout()
        exercise_layout.addWidget(QLabel("種目:"))
        self.exercise_combo = QComboBox()
        self.exercise_combo.currentTextChanged.connect(self.on_exercise_changed)
        exercise_layout.addWidget(self.exercise_combo)
        exercise_layout.addStretch()
        layout.addLayout(exercise_layout)
        
        # 前回記録表示
        self.previous_record_label = QLabel("前回記録: なし")
        self.previous_record_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(self.previous_record_label)
        
        # セパレータ
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # セット入力エリア
        sets_label = QLabel("セット入力")
        sets_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(sets_label)
        
        # スクロールエリア
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.sets_widget = QWidget()
        self.sets_layout = QVBoxLayout(self.sets_widget)
        self.scroll_area.setWidget(self.sets_widget)
        layout.addWidget(self.scroll_area)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        
        self.add_set_button = QPushButton("セット追加")
        self.add_set_button.clicked.connect(self.add_set)
        button_layout.addWidget(self.add_set_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_workout)
        self.save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # 初期セット追加
        self.add_set()
    
    def load_exercises(self):
        """種目読み込み"""
        try:
            all_exercises = self.db_manager.get_all_exercises()
            
            # カテゴリ別に種目を分類
            self.exercises_by_category = {}
            for exercise in all_exercises:
                category = exercise.category
                if category not in self.exercises_by_category:
                    self.exercises_by_category[category] = []
                self.exercises_by_category[category].append(exercise)
            
            # カテゴリコンボボックスを設定
            self.category_combo.clear()
            self.category_combo.addItem("部位を選択してください", None)
            
            for category in EXERCISE_CATEGORIES:
                if category in self.exercises_by_category:
                    exercise_count = len(self.exercises_by_category[category])
                    self.category_combo.addItem(f"{category} ({exercise_count}種目)", category)
            
            # 種目コンボボックスを初期化
            self.exercise_combo.clear()
            self.exercise_combo.addItem("部位を先に選択してください", None)
            self.exercise_combo.setEnabled(False)
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "種目データの読み込みに失敗しました", str(e))
    
    def on_category_changed(self):
        """部位変更時の処理"""
        selected_category = self.category_combo.currentData()
        
        # 種目コンボボックスをクリア
        self.exercise_combo.clear()
        self.current_exercise_id = None
        self.previous_record_label.setText("前回記録: なし")
        
        if selected_category is None:
            self.exercise_combo.addItem("部位を先に選択してください", None)
            self.exercise_combo.setEnabled(False)
            return
        
        # 選択された部位の種目を読み込み
        self.exercise_combo.setEnabled(True)
        self.exercise_combo.addItem("種目を選択してください", None)
        
        if selected_category in self.exercises_by_category:
            exercises = self.exercises_by_category[selected_category]
            for exercise in exercises:
                self.exercise_combo.addItem(exercise.display_name(), exercise.id)
    
    def on_exercise_changed(self):
        """種目変更時の処理"""
        self.current_exercise_id = self.exercise_combo.currentData()
        if self.current_exercise_id:
            self.load_previous_record()
        else:
            self.previous_record_label.setText("前回記録: なし")
    
    def load_previous_record(self):
        """前回記録読み込み"""
        if not self.current_exercise_id:
            return
        
        try:
            last_sets = self.db_manager.get_last_exercise_record(self.current_exercise_id)
            if last_sets:
                # 最新のワークアウトの最初のセットを表示
                first_set = last_sets[0]
                self.previous_record_label.setText(
                    f"前回記録: {first_set.weight}kg × {first_set.reps}回"
                )
                
                # 最初のセットに前回データをコピー
                if self.set_widgets:
                    self.set_widgets[0].set_previous_data(first_set.weight, first_set.reps)
            else:
                self.previous_record_label.setText("前回記録: なし")
                
        except Exception as e:
            self.show_error("データ読み込みエラー", "前回記録の読み込みに失敗しました", str(e))
    
    def add_set(self):
        """セット追加"""
        set_number = len(self.set_widgets) + 1
        set_widget = SetWidget(set_number)
        
        # 削除ボタンのイベント接続
        set_widget.delete_button.clicked.connect(lambda: self.remove_set(set_widget))
        
        self.set_widgets.append(set_widget)
        self.sets_layout.addWidget(set_widget)
        
        # スクロールを下に移動（修正版）
        try:
            # QTimer を使って少し遅らせてスクロール
            from PySide6.QtCore import QTimer
            QTimer.singleShot(10, self.scroll_to_bottom)
        except:
            pass  # スクロール失敗は致命的ではない
    
    def scroll_to_bottom(self):
        """スクロールエリアを最下部に移動"""
        try:
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except:
            pass
    
    def remove_set(self, set_widget):
        """セット削除"""
        if len(self.set_widgets) <= 1:
            self.show_warning("警告", "最低1セットは必要です")
            return
        
        self.sets_layout.removeWidget(set_widget)
        self.set_widgets.remove(set_widget)
        set_widget.deleteLater()
        
        # セット番号を振り直し
        for i, widget in enumerate(self.set_widgets):
            widget.set_number = i + 1
            # ラベルを更新
            labels = widget.findChildren(QLabel)
            if labels:
                labels[0].setText(f"セット#{i + 1}")
    
    def save_workout(self):
        """ワークアウト保存（検証付き）"""
        if not self.set_widgets:
            self.show_warning("警告", "保存するセットがありません")
            return
        
        if self.current_exercise_id is None:
            self.show_warning("警告", "種目を選択してください")
            return
        
        # 全セットのデータ検証
        validation_errors = []
        for i, set_widget in enumerate(self.set_widgets):
            set_data = set_widget.get_set_data()
            valid, error = validate_set_data(set_data['weight'], set_data['reps'])
            if not valid:
                validation_errors.append(f"セット#{i+1}: {error}")
        
        if validation_errors:
            error_message = "以下のエラーを修正してください:\n\n" + "\n".join(validation_errors)
            self.show_warning("入力エラー", error_message)
            return
        
        try:
            # ワークアウト作成または取得
            workout_date = self.date_edit.date().toPython()
            workout = self.db_manager.get_workout_by_date(workout_date)
            
            if not workout:
                workout_id = self.db_manager.add_workout(workout_date)
                if not workout_id:
                    self.show_error("保存エラー", "ワークアウトの作成に失敗しました")
                    return
            else:
                workout_id = workout.id
            
            # セットデータ保存
            success_count = 0
            for i, set_widget in enumerate(self.set_widgets):
                set_data = set_widget.get_set_data()
                
                set_record = Set(
                    id=None,
                    workout_id=workout_id,
                    exercise_id=self.current_exercise_id,
                    set_number=i + 1,
                    weight=set_data['weight'],
                    reps=set_data['reps']
                )
                
                if self.db_manager.add_set_safe(set_record):
                    success_count += 1
            
            if success_count == len(self.set_widgets):
                self.show_info("保存完了", f"{success_count}セットを保存しました")
                # 入力フィールドをクリア
                self.clear_sets()
            else:
                self.show_warning("部分保存", 
                                f"{success_count}/{len(self.set_widgets)}セットを保存しました")
                
        except Exception as e:
            self.show_error("保存エラー", "ワークアウトの保存に失敗しました", str(e))
    
    def clear_sets(self):
        """セット入力クリア"""
        # 全セットウィジェット削除
        for set_widget in self.set_widgets:
            self.sets_layout.removeWidget(set_widget)
            set_widget.deleteLater()
        
        self.set_widgets.clear()
        
        # 新しいセットを1つ追加
        self.add_set()