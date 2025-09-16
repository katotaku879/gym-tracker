# ui/base_tab.py - 共通基底クラス
from PySide6.QtWidgets import QWidget, QMessageBox
from typing import Optional
import logging

class BaseTab(QWidget):
    """タブ基底クラス"""
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    def show_error(self, title: str, message: str, details: Optional[str] = None):
        """エラー表示"""
        self.logger.error(f"{title}: {message}")
        if details is not None:
            self.logger.error(f"Details: {details}")
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if details is not None:
            msg_box.setDetailedText(details)
        msg_box.exec()

    def show_warning(self, title: str, message: str):
        """警告表示"""
        self.logger.warning(f"{title}: {message}")
        QMessageBox.warning(self, title, message)

    def show_info(self, title: str, message: str):
        """情報表示"""
        self.logger.info(f"{title}: {message}")
        QMessageBox.information(self, title, message)

    def safe_execute(self, operation, error_title: str = "エラー", error_message: str = "操作に失敗しました"):
        """安全な操作実行"""
        try:
            return operation()
        except Exception as e:
            self.show_error(error_title, error_message, str(e))
            return None