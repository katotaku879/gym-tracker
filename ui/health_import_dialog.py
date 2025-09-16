# ui/health_import_dialog.py - 完全版（PySide6対応）
"""
Appleヘルスデータ移行ダイアログ
"""

from typing import Dict, Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFileDialog, QTextEdit,
                               QProgressBar, QGroupBox, QMessageBox,
                               QDialogButtonBox, QCheckBox)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QFont

class ImportWorker(QObject):
    """インポート処理用ワーカー"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, db_manager, xml_path):
        super().__init__()
        self.db_manager = db_manager
        self.xml_path = xml_path
    
    def run(self):
        """インポート実行"""
        try:
            from utils.health_data_importer import HealthDataImporter
            
            importer = HealthDataImporter(self.db_manager)
            
            self.progress.emit("XMLファイルを解析中...")
            result = importer.import_from_export_xml(self.xml_path)
            
            self.progress.emit("インポート完了！")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class HealthImportDialog(QDialog):
    """Appleヘルスデータ移行ダイアログ"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.xml_path = ""
        self.preview_data = None
        self.worker_thread = None
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """UI初期化"""
        self.setWindowTitle("📱 Appleヘルスデータ移行")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("📱 Appleヘルスアプリから体重データを移行")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        # 手順説明
        self.create_instructions(layout)
        
        # ファイル選択エリア
        self.create_file_selection(layout)
        
        # プレビューエリア
        self.create_preview_area(layout)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # ボタンエリア
        self.create_buttons(layout)
        
    def create_instructions(self, layout):
        """手順説明作成"""
        instructions_group = QGroupBox("📋 移行手順")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = """
1. 📱 iPhoneのヘルスアプリを開く
2. 👤 右上のプロフィールアイコンをタップ
3. 📤 「すべてのヘルスデータを書き出す」を選択
4. 💾 「データを書き出す」をタップ
5. 📧 AirDropまたはメールでPCに送信
6. 📂 受信したZIPファイルを展開
7. 📄 「export.xml」ファイルを選択してインポート

⚠️ 注意: XMLファイルは大きい場合があります（数十MB〜数百MB）
        """
        
        instructions_label = QLabel(instructions_text.strip())
        instructions_label.setStyleSheet("""
            QLabel {
                color: #34495e;
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                line-height: 1.4;
            }
        """)
        instructions_layout.addWidget(instructions_label)
        
        layout.addWidget(instructions_group)
    
    def create_file_selection(self, layout):
        """ファイル選択エリア作成"""
        file_group = QGroupBox("📄 XMLファイル選択")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("ファイルが選択されていません")
        self.file_path_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        file_layout.addWidget(self.file_path_label)
        
        select_file_btn = QPushButton("📂 ファイル選択")
        select_file_btn.clicked.connect(self.select_xml_file)
        select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        file_layout.addWidget(select_file_btn)
        
        preview_btn = QPushButton("👁️ プレビュー")
        preview_btn.clicked.connect(self.preview_data_func)
        preview_btn.setEnabled(False)
        self.preview_btn = preview_btn
        file_layout.addWidget(preview_btn)
        
        layout.addWidget(file_group)
    
    def create_preview_area(self, layout):
        """プレビューエリア作成"""
        self.preview_group = QGroupBox("👁️ データプレビュー")
        self.preview_group.setVisible(False)
        preview_layout = QVBoxLayout(self.preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(self.preview_group)
    
    def create_buttons(self, layout):
        """ボタンエリア作成"""
        button_layout = QHBoxLayout()
        
        # 重複データの扱いチェックボックス
        self.overwrite_check = QCheckBox("既存データがある日付は上書きする")
        self.overwrite_check.setChecked(True)
        button_layout.addWidget(self.overwrite_check)
        
        button_layout.addStretch()
        
        # インポート実行ボタン
        self.import_btn = QPushButton("📥 インポート実行")
        self.import_btn.clicked.connect(self.start_import)
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.import_btn)
        
        # キャンセルボタン
        cancel_btn = QPushButton("❌ キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def select_xml_file(self):
        """XMLファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Appleヘルス export.xml ファイルを選択",
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            self.xml_path = file_path
            # ファイル名のみ表示（パスが長い場合）
            import os
            filename = os.path.basename(file_path)
            self.file_path_label.setText(f"選択中: {filename}")
            self.file_path_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            self.preview_btn.setEnabled(True)
            self.import_btn.setEnabled(True)
    
    def preview_data_func(self):
        """データプレビュー"""
        if not self.xml_path:
            return
        
        try:
            from utils.health_data_importer import HealthDataImporter
            
            importer = HealthDataImporter(self.db_manager)
            self.preview_data = importer.preview_import_data(self.xml_path)
            
            # プレビューテキスト生成
            preview_text = self.generate_preview_text(self.preview_data)
            
            self.preview_text.setPlainText(preview_text)
            self.preview_group.setVisible(True)
            
            # ダイアログサイズを調整
            self.resize(600, 700)
            
        except Exception as e:
            QMessageBox.critical(self, "プレビューエラー", 
                               f"データのプレビューに失敗しました:\n{str(e)}")
    
    def generate_preview_text(self, preview_data: Dict) -> str:
        """プレビューテキスト生成"""
        lines = []
        
        # 体重データ
        weight_data = preview_data.get('weight', {})
        lines.append("📊 体重データ")
        lines.append(f"  件数: {weight_data.get('count', 0)}件")
        
        if weight_data.get('date_range'):
            stats = weight_data['date_range']
            lines.append(f"  期間: {stats.get('start_date')} 〜 {stats.get('end_date')}")
            if stats.get('min_value') and stats.get('max_value'):
                lines.append(f"  範囲: {stats['min_value']:.1f}kg 〜 {stats['max_value']:.1f}kg")
                lines.append(f"  平均: {stats.get('average', 0):.1f}kg")
        
        lines.append("")
        
        # 体脂肪率データ  
        body_fat_data = preview_data.get('body_fat', {})
        lines.append("📈 体脂肪率データ")
        lines.append(f"  件数: {body_fat_data.get('count', 0)}件")
        
        if body_fat_data.get('date_range'):
            stats = body_fat_data['date_range']
            lines.append(f"  期間: {stats.get('start_date')} 〜 {stats.get('end_date')}")
            if stats.get('min_value') and stats.get('max_value'):
                lines.append(f"  範囲: {stats['min_value']:.1f}% 〜 {stats['max_value']:.1f}%")
                lines.append(f"  平均: {stats.get('average', 0):.1f}%")
        
        lines.append("")
        lines.append("📋 サンプルデータ（最初の5件）:")
        
        # 体重サンプル
        weight_samples = weight_data.get('sample', [])
        if weight_samples:
            lines.append("  体重:")
            for sample in weight_samples[:5]:
                lines.append(f"    {sample['date']}: {sample['weight']}kg")
        
        return "\n".join(lines)
    
    def start_import(self):
        """インポート開始"""
        if not self.xml_path:
            return
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self, "📥 インポート確認",
            f"Appleヘルスデータをインポートしますか？\n\n"
            f"選択ファイル: {self.xml_path}\n"
            f"既存データの上書き: {'はい' if self.overwrite_check.isChecked() else 'いいえ'}",
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
        self.worker_thread = QThread()
        self.worker = ImportWorker(self.db_manager, self.xml_path)
        self.worker.moveToThread(self.worker_thread)
        
        # シグナル接続
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_import_finished)
        self.worker.error.connect(self.on_import_error)
        self.worker.progress.connect(self.on_import_progress)
        
        # スレッド開始
        self.worker_thread.start()
    
    def on_import_progress(self, message: str):
        """インポート進捗"""
        self.progress_bar.setFormat(message)
    
    def on_import_finished(self, result: Dict):
        """インポート完了"""
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        self.progress_bar.setVisible(False)
        
        # 結果表示
        message = f"""
📥 データ移行が完了しました！

📊 移行結果:
• 体重データ: {result.get('weight_records', 0)}件
• 体脂肪率データ: {result.get('body_fat_records', 0)}件
• 合計: {result.get('total', 0)}件

✅ GymTrackerの体組成タブでデータを確認できます。
        """
        
        QMessageBox.information(self, "✅ 移行完了", message.strip())
        self.accept()
    
    def on_import_error(self, error_message: str):
        """インポートエラー"""
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        QMessageBox.critical(self, "❌ インポートエラー", 
                           f"データの移行中にエラーが発生しました:\n\n{error_message}")
    
    def closeEvent(self, event):
        """ダイアログ終了時の処理"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()