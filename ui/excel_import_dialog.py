# ui/excel_import_dialog.py
"""
Excelファイル一括インポートダイアログ
"""
import os

from typing import Dict, Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QFileDialog, QTextEdit,
                               QProgressBar, QGroupBox, QMessageBox,
                               QDialogButtonBox, QCheckBox, QTabWidget,
                               QTableWidget, QTableWidgetItem, QWidget)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QFont

class ExcelImportWorker(QObject):
    """Excel一括インポート処理用ワーカー"""
    finished = Signal(dict)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, db_manager, excel_path, overwrite):
        super().__init__()
        self.db_manager = db_manager
        self.excel_path = excel_path
        self.overwrite = overwrite
    
    def run(self):
        """インポート実行"""
        try:
            from utils.excel_body_stats_importer import ExcelBodyStatsImporter
            
            importer = ExcelBodyStatsImporter(self.db_manager)
            
            self.progress.emit("Excelファイルを解析中...")
            result = importer.import_from_excel(self.excel_path, self.overwrite)
            
            self.progress.emit("インポート完了！")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class ExcelImportDialog(QDialog):
    """Excel一括インポートダイアログ"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.excel_path = ""
        self.preview_data = None
        self.worker_thread = None
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """UI初期化"""
        self.setWindowTitle("📊 Excel一括インポート - 体組成データ")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # タイトル
        title_label = QLabel("📊 Excelファイルから体組成データを一括インポート")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        # 手順説明
        self.create_instructions(layout)
        
        # ファイル選択エリア
        self.create_file_selection(layout)
        
        # タブウィジェット（プレビュー・統計）
        self.create_tab_widget(layout)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # ボタンエリア
        self.create_buttons(layout)
        
    def create_instructions(self, layout):
        """手順説明作成"""
        instructions_group = QGroupBox("📋 対応形式")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = """
✅ 対応するExcelファイル形式:
• 日付、体重、体脂肪率、筋肉量を含むファイル
• ヘッダー行があるファイル（自動検出）
• .xlsx、.xls ファイル

📊 インポートされるデータ:
• 📅 日付（必須）
• ⚖️ 体重（kg）
• 📈 体脂肪率（%）
• 💪 筋肉量（kg）

⚠️ 注意事項:
• 同じ日付のデータがある場合、上書き確認が表示されます
• 不正な値は自動的にスキップされます
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
        file_group = QGroupBox("📄 Excelファイル選択")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("ファイルが選択されていません")
        self.file_path_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        file_layout.addWidget(self.file_path_label)
        
        select_file_btn = QPushButton("📂 ファイル選択")
        select_file_btn.clicked.connect(self.select_excel_file)
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
    
    def create_tab_widget(self, layout):
        """タブウィジェット作成"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setVisible(False)
        
        # プレビュータブ
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        self.tab_widget.addTab(self.preview_tab, "📊 データプレビュー")
        
        # 統計タブ
        self.stats_tab = QWidget()
        stats_layout = QVBoxLayout(self.stats_tab)
        
        self.stats_table = QTableWidget()
        stats_layout.addWidget(self.stats_table)
        
        self.tab_widget.addTab(self.stats_tab, "📈 統計情報")
        
        layout.addWidget(self.tab_widget)
    
    def create_buttons(self, layout):
        """ボタンエリア作成"""
        button_layout = QHBoxLayout()
        
        # 上書き設定チェックボックス
        self.overwrite_check = QCheckBox("既存データがある日付は上書きする")
        self.overwrite_check.setChecked(True)
        button_layout.addWidget(self.overwrite_check)
        
        button_layout.addStretch()
        
        # インポート実行ボタン
        self.import_btn = QPushButton("📥 一括インポート実行")
        self.import_btn.clicked.connect(self.start_import)
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
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
    
    def select_excel_file(self):
        """Excelファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Excelファイルを選択",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.excel_path = file_path
            # ファイル名のみ表示
            import os
            filename = os.path.basename(file_path)
            self.file_path_label.setText(f"選択中: {filename}")
            self.file_path_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            self.preview_btn.setEnabled(True)
            self.import_btn.setEnabled(True)
    
    def preview_data_func(self):
        """データプレビュー"""
        if not self.excel_path:
            return
        
        try:
            from utils.excel_body_stats_importer import ExcelBodyStatsImporter
            
            importer = ExcelBodyStatsImporter(self.db_manager)
            self.preview_data = importer.preview_import_data(self.excel_path)
            
            if 'error' in self.preview_data:
                QMessageBox.critical(self, "プレビューエラー", 
                                   f"プレビューの生成に失敗しました:\n{self.preview_data['error']}")
                return
            
            # プレビューテキスト生成
            preview_text = self.generate_preview_text(self.preview_data)
            self.preview_text.setPlainText(preview_text)
            
            # 統計テーブル更新
            self.update_stats_table(self.preview_data)
            
            self.tab_widget.setVisible(True)
            
            # ダイアログサイズを調整
            self.resize(700, 800)
            
        except Exception as e:
            QMessageBox.critical(self, "プレビューエラー", 
                               f"データのプレビューに失敗しました:\n{str(e)}")
    
    def generate_preview_text(self, preview_data: Dict) -> str:
        """プレビューテキスト生成"""
        if not preview_data.get('success'):
            return f"エラー: {preview_data.get('error', '不明なエラー')}"
        
        lines = []
        
        # 基本情報
        lines.append("📊 インポート予定データ")
        lines.append(f"  総レコード数: {preview_data.get('total_records', 0)}件")
        
        date_range = preview_data.get('date_range', {})
        if date_range:
            lines.append(f"  期間: {date_range.get('start')} 〜 {date_range.get('end')}")
        
        lines.append("")
        
        # データ種類
        data_types = preview_data.get('data_types', {})
        lines.append("📋 データ種別:")
        lines.append(f"  体重データ: {data_types.get('weight', 0)}件")
        lines.append(f"  体脂肪率データ: {data_types.get('body_fat', 0)}件")
        lines.append(f"  筋肉量データ: {data_types.get('muscle_mass', 0)}件")
        
        lines.append("")
        lines.append("🔍 サンプルデータ（最初の5件）:")
        
        # サンプルデータ
        sample_data = preview_data.get('sample_data', [])
        for i, sample in enumerate(sample_data):
            lines.append(f"  {i+1}. {sample.get('date')}")
            if sample.get('weight'):
                lines.append(f"     体重: {sample['weight']:.1f}kg")
            if sample.get('body_fat_percentage'):
                lines.append(f"     体脂肪率: {sample['body_fat_percentage']:.1f}%")
            if sample.get('muscle_mass'):
                lines.append(f"     筋肉量: {sample['muscle_mass']:.1f}kg")
        
        return "\n".join(lines)
    
    def update_stats_table(self, preview_data: Dict):
        """統計テーブル更新"""
        stats = preview_data.get('stats', {})
        
        # テーブル設定
        rows_data = []
        
        for data_type, data_stats in stats.items():
            if data_type == 'weight':
                type_name = "体重 (kg)"
            elif data_type == 'body_fat':
                type_name = "体脂肪率 (%)"
            elif data_type == 'muscle_mass':
                type_name = "筋肉量 (kg)"
            else:
                continue
            
            rows_data.append([
                type_name,
                f"{data_stats.get('min', 0):.1f}",
                f"{data_stats.get('max', 0):.1f}",
                f"{data_stats.get('avg', 0):.1f}"
            ])
        
        self.stats_table.setRowCount(len(rows_data))
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["項目", "最小値", "最大値", "平均値"])
        
        for row, data in enumerate(rows_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.stats_table.setItem(row, col, item)
        
        # 列幅調整
        self.stats_table.resizeColumnsToContents()
    
    def start_import(self):
        """インポート開始"""
        if not self.excel_path:
            return
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self, "📥 一括インポート確認",
            f"Excelファイルから体組成データを一括インポートしますか？\n\n"
            f"選択ファイル: {os.path.basename(self.excel_path)}\n"
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
        self.worker = ExcelImportWorker(
            self.db_manager, 
            self.excel_path, 
            self.overwrite_check.isChecked()
        )
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
📊 Excel一括インポートが完了しました！

📥 インポート結果:
• 新規追加: {result.get('imported', 0)}件
• 既存更新: {result.get('updated', 0)}件
• スキップ: {result.get('skipped', 0)}件
• エラー: {result.get('errors', 0)}件
• 処理総数: {result.get('total_processed', 0)}件

✅ GymTrackerの体組成タブでデータを確認できます。
        """
        
        QMessageBox.information(self, "✅ 一括インポート完了", message.strip())
        self.accept()
    
    def on_import_error(self, error_message: str):
        """インポートエラー"""
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        QMessageBox.critical(self, "❌ インポートエラー", 
                           f"Excel一括インポート中にエラーが発生しました:\n\n{error_message}")
    
    def closeEvent(self, event):
        """ダイアログ終了時の処理"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()