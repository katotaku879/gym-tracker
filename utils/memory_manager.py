# utils/memory_manager.py
import gc
import psutil
import os
from PySide6.QtWidgets import QMessageBox

class MemoryManager:
    """メモリ管理クラス"""
    
    @staticmethod
    def get_memory_usage():
        """現在のメモリ使用量取得（MB）"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def check_memory_limit(limit_mb=500):
        """メモリ制限チェック"""
        current_memory = MemoryManager.get_memory_usage()
        if current_memory > limit_mb:
            gc.collect()  # ガベージコレクション実行
            new_memory = MemoryManager.get_memory_usage()
            if new_memory > limit_mb:
                QMessageBox.warning(None, "メモリ警告",
                    f"メモリ使用量が{current_memory:.1f}MBに達しています。\n"
                    "アプリケーションの動作が遅くなる可能性があります。")
                return False
        return True
    
    @staticmethod
    def force_cleanup():
        """強制クリーンアップ"""
        gc.collect()
        if hasattr(gc, 'set_debug'):
            gc.set_debug(0)