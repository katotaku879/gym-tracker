# ui/goals_tab_v2.py - 3セット方式専用の目標タブ（1RM基準完全削除）

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QFrame, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.base_tab import BaseTab
from ui.goal_dialog_v2 import GoalDialogV2
from ui.goal_widget_v2 import GoalWidgetV2

class GoalsTabV2(BaseTab):
    """3セット方式専用の目標タブ"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.init_ui()
        self.load_goals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QVBoxLayout(self)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🎯 トレーニング目標（3セット方式）")
        title_label.setStyleSheet("QLabel { font-size: 20px; font-weight: bold; color: #2c3e50; }")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 目標追加ボタン
        self.add_goal_button = QPushButton("➕ 新しい目標を追加")
        self.add_goal_button.clicked.connect(self.add_goal)
        self.add_goal_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        header_layout.addWidget(self.add_goal_button)
        
        layout.addLayout(header_layout)
        
        # 説明テキスト
        desc_label = QLabel("💡 3セット方式: 「重量×回数×セット数」で具体的な目標を設定し、実際のワークアウトで達成セット数を追跡します")
        desc_label.setStyleSheet("""
            QLabel { 
                color: #7f8c8d; 
                font-style: italic; 
                padding: 10px; 
                background-color: #f8f9fa; 
                border-left: 4px solid #3498db; 
                margin: 10px 0;
            }
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 達成可能な目標の通知エリア
        self.notification_frame = QFrame()
        self.notification_frame.setVisible(False)
        self.notification_layout = QVBoxLayout(self.notification_frame)
        layout.addWidget(self.notification_frame)
        
        # 目標一覧エリア
        self.goals_scroll = QScrollArea()
        self.goals_scroll.setWidgetResizable(True)
        self.goals_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.goals_container = QWidget()
        self.goals_layout = QVBoxLayout(self.goals_container)
        self.goals_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.goals_scroll.setWidget(self.goals_container)
        layout.addWidget(self.goals_scroll)
        
        # 下部ボタン
        bottom_layout = QHBoxLayout()
        
        # 一括進捗更新ボタン
        self.update_all_btn = QPushButton("🔄 全目標の進捗を更新")
        self.update_all_btn.clicked.connect(self.update_all_progress)
        self.update_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # 統計情報ボタン
        self.stats_btn = QPushButton("📊 目標統計")
        self.stats_btn.clicked.connect(self.show_goals_statistics)
        self.stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        bottom_layout.addWidget(self.update_all_btn)
        bottom_layout.addWidget(self.stats_btn)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
    
    def load_goals(self):
        """目標一覧を読み込み"""
        try:
            # 既存のウィジェットをクリア
            while self.goals_layout.count():
                child = self.goals_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # 3セット方式の目標を取得
            goal_data_list = self.db_manager.get_all_goals_v2()
            
            if not goal_data_list:
                # 目標がない場合の表示
                empty_widget = self.create_empty_state()
                self.goals_layout.addWidget(empty_widget)
                self.notification_frame.setVisible(False)
                return
            
            # 目標をカテゴリ別に整理
            categories = {}
            for goal_data in goal_data_list:
                category = goal_data['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(goal_data)
            
            # カテゴリ別に表示
            for category in ["脚", "胸", "背中", "肩", "腕"]:
                if category in categories:
                    # カテゴリヘッダー
                    category_label = QLabel(f"💪 {category}")
                    category_label.setStyleSheet("""
                        QLabel { 
                            font-size: 16px; 
                            font-weight: bold; 
                            color: #34495e; 
                            margin: 15px 0 10px 0;
                            border-bottom: 2px solid #bdc3c7;
                            padding-bottom: 5px;
                        }
                    """)
                    self.goals_layout.addWidget(category_label)
                    
                    # カテゴリ内の目標
                    for goal_data in categories[category]:
                        goal_widget = GoalWidgetV2(goal_data)
                        goal_widget.editRequested.connect(self.edit_goal)
                        goal_widget.deleteRequested.connect(self.delete_goal)
                        goal_widget.achieveRequested.connect(self.achieve_goal)
                        
                        self.goals_layout.addWidget(goal_widget)
            
            # 達成可能な目標の通知を更新
            self.update_achievement_notifications()
            
        except Exception as e:
            self.logger.error(f"Failed to load goals: {e}")
            self.show_error("読み込みエラー", "目標データの読み込みに失敗しました", str(e))
    
    def create_empty_state(self) -> QWidget:
        """目標がない場合の表示"""
        empty_widget = QFrame()
        empty_widget.setStyleSheet("""
            QFrame {
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
                padding: 40px;
            }
        """)
        
        empty_layout = QVBoxLayout(empty_widget)
        
        # アイコン
        icon_label = QLabel("🎯")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("QLabel { font-size: 48px; border: none; }")
        
        # メッセージ
        message_label = QLabel("まだ目標が設定されていません")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("QLabel { font-size: 18px; font-weight: bold; color: #7f8c8d; border: none; }")
        
        # サブメッセージ
        sub_message_label = QLabel("「新しい目標を追加」ボタンから最初の目標を設定しましょう！")
        sub_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_message_label.setStyleSheet("QLabel { font-size: 14px; color: #95a5a6; border: none; }")
        sub_message_label.setWordWrap(True)
        
        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(message_label)
        empty_layout.addWidget(sub_message_label)
        
        return empty_widget
    
    def update_achievement_notifications(self):
        """達成可能な目標の通知を更新"""
        try:
            achievable_goals = self.db_manager.get_achievable_goals_v2()
            
            # 通知をクリア
            while self.notification_layout.count():
                child = self.notification_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            if not achievable_goals:
                self.notification_frame.setVisible(False)
                return
            
            # 通知フレームを作成
            notification_widget = QFrame()
            notification_widget.setStyleSheet("""
                QFrame {
                    background-color: #fff3cd;
                    border: 2px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 10px 0;
                }
            """)
            
            notification_layout = QVBoxLayout(notification_widget)
            
            # ヘッダー
            header_label = QLabel("🎉 あと少しで達成できる目標があります！")
            header_label.setStyleSheet("QLabel { font-weight: bold; color: #856404; border: none; }")
            notification_layout.addWidget(header_label)
            
            # 目標リスト（最大3件）
            for goal_data in achievable_goals[:3]:
                goal = goal_data['goal']
                exercise_name = goal_data['exercise_name']
                remaining = goal.remaining_sets()
                
                text = f"💪 {exercise_name}: あと{remaining}セットで達成！ ({goal.target_description()})"
                label = QLabel(text)
                label.setStyleSheet("QLabel { color: #856404; font-weight: normal; border: none; }")
                notification_layout.addWidget(label)
            
            if len(achievable_goals) > 3:
                more_label = QLabel(f"他{len(achievable_goals) - 3}件の目標も達成間近です。")
                more_label.setStyleSheet("QLabel { color: #856404; font-style: italic; border: none; }")
                notification_layout.addWidget(more_label)
            
            self.notification_layout.addWidget(notification_widget)
            self.notification_frame.setVisible(True)
            
        except Exception as e:
            self.logger.error(f"Failed to update achievement notifications: {e}")
    
    def add_goal(self):
        """新しい目標を追加"""
        dialog = GoalDialogV2(self.db_manager, parent=self)
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
                self.show_warning("入力エラー", "目標期限を入力してください。")
                return
            
            # データベースに保存
            goal_id = self.db_manager.add_goal_v2(goal_data)
            if goal_id:
                self.show_info(
                    "目標追加", 
                    f"✅ 新しい目標を追加しました！\n\n"
                    f"🎯 {goal_data.target_description()}\n"
                    f"📅 期限: {goal_data.target_month}\n\n"
                    f"頑張って達成しましょう 💪"
                )
                self.load_goals()
            else:
                self.show_error("保存エラー", "目標の保存に失敗しました。")
    
    def edit_goal(self, goal):
        """目標を編集"""
        dialog = GoalDialogV2(self.db_manager, goal, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_goal = dialog.get_goal_data()
            
            if self.db_manager.update_goal_v2(updated_goal):
                self.show_info("目標更新", "✅ 目標を更新しました！")
                self.load_goals()
            else:
                self.show_error("更新エラー", "目標の更新に失敗しました。")
    
    def delete_goal(self, goal):
        """目標を削除"""
        reply = QMessageBox.question(
            self, "目標削除", 
            f"目標「{goal.target_description()}」を削除しますか？\n\n"
            f"この操作は元に戻せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_goal_v2(goal.id):
                self.show_info("目標削除", "🗑️ 目標を削除しました。")
                self.load_goals()
            else:
                self.show_error("削除エラー", "目標の削除に失敗しました。")
    
    def achieve_goal(self, goal):
        """目標を達成済みにマーク"""
        reply = QMessageBox.question(
            self, "目標達成", 
            f"目標「{goal.target_description()}」を達成済みにマークしますか？\n\n"
            f"🎉 おめでとうございます！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 目標を達成済みに更新
            goal.achieved = True
            goal.current_achieved_sets = goal.target_sets
            
            if self.db_manager.update_goal_v2(goal):
                self.show_info(
                    "目標達成", 
                    "🎉 おめでとうございます！\n\n"
                    "目標を達成済みにマークしました！🏆"
                )
                self.load_goals()
            else:
                self.show_error("更新エラー", "目標の更新に失敗しました。")
    
    def update_all_progress(self):
        """全目標の進捗を更新"""
        try:
            goals = self.db_manager.get_all_goals_v2()
            updated_count = 0
            
            for goal_data in goals:
                goal = goal_data['goal']
                if not goal.achieved:
                    if self.db_manager.calculate_goal_progress_v2(goal.id):
                        updated_count += 1
            
            if updated_count > 0:
                self.show_info("進捗更新", f"📊 {updated_count}個の目標の進捗を更新しました！")
                self.load_goals()
            else:
                self.show_info("進捗更新", "更新する進捗データがありませんでした。\nトレーニング記録を追加してから再度お試しください。")
                
        except Exception as e:
            self.logger.error(f"Failed to update progress: {e}")
            self.show_error("更新エラー", "進捗の更新に失敗しました。")
    
    def show_goals_statistics(self):
        """目標統計を表示"""
        try:
            goals = self.db_manager.get_all_goals_v2()
            
            total_goals = len(goals)
            achieved_goals = len([g for g in goals if g['goal'].achieved])
            active_goals = total_goals - achieved_goals
            achievement_rate = int((achieved_goals / total_goals * 100)) if total_goals > 0 else 0
            
            stats_text = (
                f"📊 目標統計情報\n\n"
                f"総目標数: {total_goals}個\n"
                f"達成済み: {achieved_goals}個\n"
                f"挑戦中: {active_goals}個\n"
                f"達成率: {achievement_rate}%"
            )
            
            self.show_info("目標統計", stats_text)
            
        except Exception as e:
            self.logger.error(f"Failed to show statistics: {e}")
            self.show_error("統計エラー", "統計の表示に失敗しました。")
    
    def refresh_data(self):
        """データ再読み込み（外部から呼び出し用）"""
        self.load_goals()