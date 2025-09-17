import time
import psutil
import logging
from functools import wraps
from typing import Callable, Any

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    @staticmethod
    def measure_time(func_name: str = None):
        """実行時間測定デコレーター"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                
                execution_time = end_time - start_time
                name = func_name or func.__name__
                
                if execution_time > 1.0:  # 1秒以上の場合は警告
                    logging.warning(f"Slow operation: {name} took {execution_time:.2f}s")
                else:
                    logging.debug(f"Performance: {name} took {execution_time:.3f}s")
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def get_memory_usage() -> float:
        """現在のメモリ使用量取得（MB）"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def log_memory_usage(operation: str):
        """メモリ使用量ログ出力"""
        memory_mb = PerformanceMonitor.get_memory_usage()
        if memory_mb > 200:  # 200MB以上で警告
            logging.warning(f"High memory usage: {operation} - {memory_mb:.1f}MB")
        else:
            logging.debug(f"Memory usage: {operation} - {memory_mb:.1f}MB")


# 使用例: 既存のメソッドにデコレーターを追加

class BodyStatsTab(BaseTab):
    
    @PerformanceMonitor.measure_time("BodyStatsTab.load_data_async")
    def load_data_async(self):
        """非同期データ読み込み（パフォーマンス測定付き）"""
        PerformanceMonitor.log_memory_usage("Before data load")
        
        # データ読み込みスレッド開始
        self.data_thread = DataLoadThread(self.db_manager)
        self.data_thread.data_loaded.connect(self.on_data_loaded)
        self.data_thread.summary_loaded.connect(self.on_summary_loaded)
        self.data_thread.error_occurred.connect(self.on_load_error)
        self.data_thread.start()
    
    @PerformanceMonitor.measure_time("BodyStatsTab.populate_table_fast")
    def populate_table_fast(self, stats_list: List[BodyStats]):
        """テーブル高速描画（パフォーマンス測定付き）"""
        PerformanceMonitor.log_memory_usage("Before table population")
        
        # 既存の実装...
        
        PerformanceMonitor.log_memory_usage("After table population")