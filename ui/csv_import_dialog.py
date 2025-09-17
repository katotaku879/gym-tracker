# ui/csv_import_dialog.py
"""
CSVワークアウトデータインポート用ダイアログ
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QComboBox,
    QCheckBox, QProgressBar, QTextEdit, QGroupBox, QGridLayout,
    QMessageBox, QLineEdit, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from utils.csv_workout_importer import CSVWorkoutImporter
import logging

class CSVImportWorker(QThread):
    """CSVインポート用ワーカースレッド"""
    
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, db_manager, csv_path, exercise_name, exercise_variation, 
                 exercise_category, overwrite):
        super().__init__()
        self.db_manager = db_manager
        self.csv_path = csv_path
        self.exercise_name = exercise_name
        self.exercise_variation = exercise_variation
        self.exercise_category = exercise_category
        self.overwrite = overwrite
    
    def run(self):
        try:
            self.progress.emit("CSVファイルを読み込み中...")
            
            importer = CSVWorkoutImporter(self.db_manager)
            result = importer.import_workout_csv(
                csv_path=self.csv_path,
                exercise_name=self.exercise_name,
                exercise_variation=self.exercise_variation,
                exercise_category=self.exercise_category,
                overwrite=self.overwrite
            )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class CSVImportDialog(QDialog):
    """CSVワークアウトデータインポートダイアログ"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.csv_path = ""
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI初期化"""
        self.setWindowTitle("🏋️‍♂️ CSVワークアウトデータインポート")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # タイトル
        title_label = QLabel("CSVワークアウトデータインポート")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # ファイル選択セクション
        file_group = QGroupBox("📁 CSVファイル選択")
        file_layout = QVBoxLayout()
        
        file_select_layout = QHBoxLayout()
        self.file_path_label = QLabel("ファイルが選択されていません")
        self.file_path_label.setStyleSheet("QLabel { color: #666; }")
        self.select_file_btn = QPushButton("📂 CSVファイルを選択")
        
        file_select_layout.addWidget(self.file_path_label, 1)
        file_select_layout.addWidget(self.select_file_btn)
        file_layout.addLayout(file_select_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 種目設定セクション
        exercise_group = QGroupBox("🏋️‍♂️ 種目設定")
        exercise_layout = QGridLayout()
        
        exercise_layout.addWidget(QLabel("種目名:"), 0, 0)
        self.exercise_name_edit = QLineEdit("スクワット")
        exercise_layout.addWidget(self.exercise_name_edit, 0, 1)
        
        exercise_layout.addWidget(QLabel("バリエーション:"), 0, 2)
        self.exercise_variation_combo = QComboBox()
        self.exercise_variation_combo.addItems([
            "バーベル", "ダンベル", "マシン", "ケーブル", "自重"
        ])
        exercise_layout.addWidget(self.exercise_variation_combo, 0, 3)
        
        exercise_layout.addWidget(QLabel("カテゴリ:"), 1, 0)
        self.exercise_category_combo = QComboBox()
        self.exercise_category_combo.addItems([
            "脚", "胸", "背中", "肩", "腕"
        ])
        exercise_layout.addWidget(self.exercise_category_combo, 1, 1)
        
        # 自動検出ボタン
        self.auto_detect_btn = QPushButton("🔍 ファイル名から自動検出")
        self.auto_detect_btn.setEnabled(False)
        exercise_layout.addWidget(self.auto_detect_btn, 1, 2, 1, 2)
        
        exercise_group.setLayout(exercise_layout)
        layout.addWidget(exercise_group)
        
        # プレビューセクション
        preview_group = QGroupBox("👀 データプレビュー")
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)
        
        self.validation_label = QLabel("")
        preview_layout.addWidget(self.validation_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # オプション設定
        options_group = QGroupBox("⚙️ インポートオプション")
        options_layout = QVBoxLayout()
        
        self.overwrite_check = QCheckBox("既存データを上書きする")
        self.overwrite_check.setChecked(False)
        options_layout.addWidget(self.overwrite_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 進捗表示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("📥 インポート開始")
        self.import_btn.setEnabled(False)
        self.cancel_btn = QPushButton("❌ キャンセル")
        
        button_layout.addStretch()
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def setup_connections(self):
        """シグナル・スロット接続"""
        self.select_file_btn.clicked.connect(self.select_csv_file)
        self.auto_detect_btn.clicked.connect(self.auto_detect_exercise)
        self.import_btn.clicked.connect(self.start_import)
        self.cancel_btn.clicked.connect(self.reject)
    
    def select_csv_file(self):
        """CSVファイル選択"""
        file_dialog = QFileDialog()
        csv_path, _ = file_dialog.getOpenFileName(
            self, "CSVファイルを選択", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if csv_path:
            self.csv_path = csv_path
            self.file_path_label.setText(os.path.basename(csv_path))
            self.file_path_label.setStyleSheet("QLabel { color: #27ae60; font-weight: bold; }")
            
            self.auto_detect_btn.setEnabled(True)
            self.validate_and_preview_csv()
    
    def auto_detect_exercise(self):
        """ファイル名から種目を自動検出"""
        if not self.csv_path:
            return
        
        filename = os.path.basename(self.csv_path).lower()
        
        # 種目マッピング
        if 'スクワット' in filename or 'squat' in filename:
            self.exercise_name_edit.setText("スクワット")
            self.exercise_variation_combo.setCurrentText("バーベル")
            self.exercise_category_combo.setCurrentText("脚")
        elif 'ベンチプレス' in filename or 'bench' in filename:
            self.exercise_name_edit.setText("ベンチプレス")
            self.exercise_variation_combo.setCurrentText("バーベル")
            self.exercise_category_combo.setCurrentText("胸")
        elif 'デッドリフト' in filename or 'deadlift' in filename:
            self.exercise_name_edit.setText("デッドリフト")
            self.exercise_variation_combo.setCurrentText("バーベル")
            self.exercise_category_combo.setCurrentText("背中")
        
        QMessageBox.information(
            self, "自動検出完了", 
            f"ファイル名から以下の種目を検出しました:\n"
            f"種目: {self.exercise_name_edit.text()}\n"
            f"バリエーション: {self.exercise_variation_combo.currentText()}\n"
            f"カテゴリ: {self.exercise_category_combo.currentText()}"
        )
    
    def validate_and_preview_csv(self):
        """CSVファイルの検証とプレビュー"""
        if not self.csv_path:
            return
        
        try:
            # CSVインポーターでファイル検証
            importer = CSVWorkoutImporter(self.db_manager)
            validation_result = importer.validate_csv_format(self.csv_path)
            
            if validation_result['valid']:
                self.validation_label.setText(
                    f"✅ 有効なCSVファイルです\n"
                    f"検出されたセット数: {len(validation_result['detected_sets'])}\n"
                    f"列数: {len(validation_result['columns'])}"
                )
                self.validation_label.setStyleSheet("QLabel { color: #27ae60; }")
                self.import_btn.setEnabled(True)
                
                # プレビューテーブル設定
                self.setup_preview_table(validation_result)
                
            else:
                error_msg = validation_result.get('error', '不明なエラー')
                self.validation_label.setText(f"❌ 無効なCSVファイル: {error_msg}")
                self.validation_label.setStyleSheet("QLabel { color: #e74c3c; }")
                self.import_btn.setEnabled(False)
                
        except Exception as e:
            self.validation_label.setText(f"❌ ファイル検証エラー: {e}")
            self.validation_label.setStyleSheet("QLabel { color: #e74c3c; }")
            self.import_btn.setEnabled(False)
    
    def setup_preview_table(self, validation_result):
        """プレビューテーブル設定"""
        sample_data = validation_result.get('sample_data', [])
        columns = validation_result.get('columns', [])
        
        if not sample_data:
            return
        
        self.preview_table.setRowCount(len(sample_data))
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)
        
        for row_idx, row_data in enumerate(sample_data):
            for col_idx, column in enumerate(columns):
                value = str(row_data.get(column, ''))
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.preview_table.setItem(row_idx, col_idx, item)
        
        self.preview_table.resizeColumnsToContents()
    
    def start_import(self):
        """インポート開始"""
        if not self.csv_path:
            QMessageBox.warning(self, "警告", "CSVファイルが選択されていません。")
            return
        
        exercise_name = self.exercise_name_edit.text().strip()
        if not exercise_name:
            QMessageBox.warning(self, "警告", "種目名を入力してください。")
            return
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self, "📥 インポート確認",
            f"以下の設定でCSVデータをインポートしますか？\n\n"
            f"ファイル: {os.path.basename(self.csv_path)}\n"
            f"種目: {exercise_name} ({self.exercise_variation_combo.currentText()})\n"
            f"カテゴリ: {self.exercise_category_combo.currentText()}\n"
            f"上書き: {'はい' if self.overwrite_check.isChecked() else 'いいえ'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.execute_import()
    
    def execute_import(self):
        """インポート実行"""
        # UIを無効化
        self.import_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 無限プログレスバー
        
        # ワーカースレッドでインポート実行
        self.worker_thread = CSVImportWorker(
            db_manager=self.db_manager,
            csv_path=self.csv_path,
            exercise_name=self.exercise_name_edit.text().strip(),
            exercise_variation=self.exercise_variation_combo.currentText(),
            exercise_category=self.exercise_category_combo.currentText(),
            overwrite=self.overwrite_check.isChecked()
        )
        
        # シグナル接続
        self.worker_thread.finished.connect(self.on_import_finished)
        self.worker_thread.error.connect(self.on_import_error)
        self.worker_thread.progress.connect(self.on_import_progress)
        
        # スレッド開始
        self.worker_thread.start()
    
    def on_import_progress(self, message):
        """インポート進捗更新"""
        self.status_label.setText(message)
    
    def on_import_finished(self, result):
        """インポート完了"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        message = (
            f"🎉 CSVインポートが完了しました！\n\n"
            f"インポートしたワークアウト: {result['imported_workouts']}件\n"
            f"インポートしたセット: {result['imported_sets']}件\n"
            f"スキップしたワークアウト: {result['skipped_workouts']}件\n"
            f"総記録数: {result['total_records']}件"
        )
        
        QMessageBox.information(self, "インポート完了", message)
        self.accept()
    
    def on_import_error(self, error_message):
        """インポートエラー"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        QMessageBox.critical(
            self, "インポートエラー",
            f"CSVインポート中にエラーが発生しました:\n\n{error_message}"
        )
        
        self.status_label.setText("インポートエラーが発生しました")
        self.status_label.setStyleSheet("QLabel { color: #e74c3c; }")