# ui/goal_widget_v2.py
"""
3セット×重量×回数方式の目標表示ウィジェット
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class GoalWidgetV2(QFrame):
    """3セット方式対応の目標表示ウィジェット"""
    
    editRequested = Signal(object)
    deleteRequested = Signal(object)
    achieveRequested = Signal(object)
    
    def __init__(self, goal_data, parent=None):
        super().__init__(parent)
        self.goal_data = goal_data
        self.goal = goal_data['goal']
        self.exercise_name = goal_data['exercise_name']
        self.init_ui()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 達成状態に応じた枠線スタイル
        if self.goal.is_achieved():
            border_color = "#27ae60"
            bg_color = "#e8f5e8"
        elif self.goal.current_achieved_sets > 0:
            border_color = "#f39c12"
            bg_color = "#fdf6e3"
        else:
            border_color = "#3498db"
            bg_color = "#ebf3fd"
        
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {border_color};
                border-radius: 10px;
                background-color: {bg_color};
                margin: 5px;
            }}
        """)
        
        # ヘッダー（種目名と状態）
        header_layout = QHBoxLayout()
        
        # 種目名
        exercise_label = QLabel(self.exercise_name)
        exercise_label.setStyleSheet("QLabel { font-weight: bold; font-size: 16px; color: #2c3e50; border: none; }")
        header_layout.addWidget(exercise_label)
        
        header_layout.addStretch()
        
        # 達成状態
        status_label = QLabel(self.goal.achievement_text())
        if self.goal.is_achieved():
            status_label.setStyleSheet("QLabel { color: #27ae60; font-weight: bold; border: none; }")
        elif self.goal.current_achieved_sets > 0:
            status_label.setStyleSheet("QLabel { color: #f39c12; font-weight: bold; border: none; }")
        else:
            status_label.setStyleSheet("QLabel { color: #3498db; font-weight: bold; border: none; }")
        
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # 目標情報
        target_info = f"🎯 目標: {self.goal.target_description()} ({self.goal.target_month}まで)"
        target_label = QLabel(target_info)
        target_label.setStyleSheet("QLabel { color: #34495e; border: none; font-size: 14px; }")
        layout.addWidget(target_label)
        
        # 進捗情報
        progress_info = f"📊 進捗: {self.goal.current_achieved_sets}/{self.goal.target_sets}セット達成"
        if self.goal.current_max_weight > 0:
            progress_info += f" (最高重量: {self.goal.current_max_weight:.1f}kg)"
        
        progress_label = QLabel(progress_info)
        progress_label.setStyleSheet("QLabel { color: #7f8c8d; border: none; font-size: 13px; }")
        layout.addWidget(progress_label)
        
        # 進捗バー（セットベース）
        progress_percentage = self.goal.progress_percentage()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress_percentage)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{progress_percentage}%")
        
        # 進捗バーのスタイル
        if progress_percentage >= 100:
            color = "#27ae60"  # 緑（達成）
        elif progress_percentage >= 60:
            color = "#f39c12"  # オレンジ（良好）
        else:
            color = "#3498db"  # 青（開始）
            
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(self.progress_bar)
        
        # 残りセット情報
        if not self.goal.is_achieved():
            remaining = self.goal.remaining_sets()
            if remaining > 0:
                remaining_text = f"💪 残り{remaining}セットで目標達成！"
                remaining_label = QLabel(remaining_text)
                remaining_label.setStyleSheet("QLabel { color: #e67e22; font-weight: bold; border: none; }")
                remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(remaining_label)
        
        # アクションボタン
        button_layout = QHBoxLayout()
        
        # 編集ボタン
        edit_btn = QPushButton("✏️ 編集")
        edit_btn.clicked.connect(lambda: self.editRequested.emit(self.goal))
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 削除ボタン
        delete_btn = QPushButton("🗑️ 削除")
        delete_btn.clicked.connect(lambda: self.deleteRequested.emit(self.goal))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # 達成ボタン（未達成の場合のみ）
        if not self.goal.is_achieved():
            achieve_btn = QPushButton("🏆 達成マーク")
            achieve_btn.clicked.connect(lambda: self.achieveRequested.emit(self.goal))
            achieve_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            button_layout.addWidget(achieve_btn)
        
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 詳細情報（折りたたみ式）
        if hasattr(self.goal, 'notes') and self.goal.notes:
            notes_label = QLabel(f"📝 {self.goal.notes}")
            notes_label.setStyleSheet("""
                QLabel { 
                    color: #7f8c8d; 
                    border: none; 
                    font-style: italic; 
                    font-size: 12px;
                    margin-top: 5px;
                }
            """)
            notes_label.setWordWrap(True)
            layout.addWidget(notes_label)