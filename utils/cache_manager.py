# utils/cache_manager.py - Pylance完全対応版

from __future__ import annotations  # Python 3.7+の前方参照サポート

import time
import logging
import pickle
import os
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from datetime import datetime, timedelta

# 型チェック時のみimport（循環import回避）
if TYPE_CHECKING:
    from database.models import BodyStats

class CacheManager:
    """シンプルなキャッシュ管理"""
    
    def __init__(self, cache_dir: str = "cache", max_age_minutes: int = 30) -> None:
        self.cache_dir = cache_dir
        self.max_age = timedelta(minutes=max_age_minutes)
        self.logger = logging.getLogger(__name__)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """キャッシュディレクトリ作成"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
                self.logger.info(f"Cache directory created: {self.cache_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create cache directory: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            
            if not os.path.exists(cache_file):
                return None
            
            # ファイル更新時刻チェック
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_time > self.max_age:
                try:
                    os.remove(cache_file)
                    self.logger.debug(f"Expired cache file removed: {cache_file}")
                except OSError as e:
                    self.logger.warning(f"Failed to remove expired cache: {e}")
                return None
            
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
                self.logger.debug(f"Cache hit for key: {key}")
                return data
                
        except Exception as e:
            self.logger.debug(f"Cache get failed for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """キャッシュに保存"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
                self.logger.debug(f"Cache set for key: {key}")
                
        except Exception as e:
            self.logger.debug(f"Cache set failed for {key}: {e}")
    
    def clear(self) -> None:
        """キャッシュクリア"""
        try:
            if not os.path.exists(self.cache_dir):
                return
                
            cleared_count = 0
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    try:
                        os.remove(os.path.join(self.cache_dir, file))
                        cleared_count += 1
                    except OSError as e:
                        self.logger.warning(f"Failed to remove cache file {file}: {e}")
            
            self.logger.debug(f"Cleared {cleared_count} cache files")
            
        except Exception as e:
            self.logger.debug(f"Cache clear failed: {e}")
    
    def clear_expired(self) -> None:
        """期限切れキャッシュのみクリア"""
        try:
            if not os.path.exists(self.cache_dir):
                return
                
            cleared_count = 0
            current_time = datetime.now()
            
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    file_path = os.path.join(self.cache_dir, file)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if current_time - file_time > self.max_age:
                            os.remove(file_path)
                            cleared_count += 1
                    except OSError as e:
                        self.logger.warning(f"Failed to process cache file {file}: {e}")
            
            if cleared_count > 0:
                self.logger.debug(f"Cleared {cleared_count} expired cache files")
                
        except Exception as e:
            self.logger.debug(f"Expired cache clear failed: {e}")
    
    def get_cache_info(self) -> Dict[str, Union[str, int, float]]:
        """キャッシュ情報取得"""
        info: Dict[str, Union[str, int, float]] = {
            "cache_dir": self.cache_dir,
            "max_age_minutes": self.max_age.total_seconds() / 60,
            "total_files": 0,
            "total_size_mb": 0.0,
            "expired_files": 0
        }
        
        try:
            if not os.path.exists(self.cache_dir):
                return info
                
            current_time = datetime.now()
            total_size = 0
            
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    file_path = os.path.join(self.cache_dir, file)
                    try:
                        stat = os.stat(file_path)
                        total_size += stat.st_size
                        info["total_files"] = int(info["total_files"]) + 1
                        
                        file_time = datetime.fromtimestamp(stat.st_mtime)
                        if current_time - file_time > self.max_age:
                            info["expired_files"] = int(info["expired_files"]) + 1
                            
                    except OSError:
                        continue
            
            info["total_size_mb"] = total_size / (1024 * 1024)
            
        except Exception as e:
            self.logger.warning(f"Failed to get cache info: {e}")
        
        return info


class CachedDatabaseManager:
    """キャッシュ機能付きDatabaseManager（ミックスイン版）"""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # 既存のDatabaseManagerの初期化は呼び出し元で行う想定
        self.cache = CacheManager()
        self.logger = logging.getLogger(__name__)
    
    def get_body_stats_optimized_cached(self) -> List[BodyStats]:
        """体組成データ取得（キャッシュ付き）"""
        cache_key = "body_stats_all"
        cached_data = self.cache.get(cache_key)
        
        if cached_data is not None:
            self.logger.debug("Body stats loaded from cache")
            return cached_data  # type: ignore
        
        # キャッシュミスの場合はDBから取得
        data = self._fetch_body_stats_from_db()
        if data:  # データが取得できた場合のみキャッシュ
            self.cache.set(cache_key, data)
            self.logger.debug("Body stats cached")
        
        return data
    
    def _fetch_body_stats_from_db(self) -> List[BodyStats]:
        """データベースから体組成データ取得（抽象メソッド）"""
        # 実際の実装は継承先で行う
        raise NotImplementedError("This method should be implemented by the actual DatabaseManager")
    
    def invalidate_body_stats_cache(self) -> None:
        """体組成キャッシュを無効化"""
        try:
            cache_file = os.path.join(self.cache.cache_dir, "body_stats_all.cache")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                self.logger.debug("Body stats cache invalidated")
        except Exception as e:
            self.logger.warning(f"Failed to invalidate cache: {e}")
    
    def clear_all_cache(self) -> None:
        """全キャッシュクリア"""
        self.cache.clear()
        self.logger.info("All cache cleared")


def test_cache_manager() -> None:
    """CacheManagerのテスト"""
    cache = CacheManager(cache_dir="test_cache", max_age_minutes=1)
    
    # テストデータ
    test_data: Dict[str, Union[str, int]] = {"test": "data", "number": 123}
    
    # キャッシュ保存
    cache.set("test_key", test_data)
    
    # キャッシュ取得
    retrieved = cache.get("test_key")
    print(f"Retrieved from cache: {retrieved}")
    
    # キャッシュ情報
    info = cache.get_cache_info()
    print(f"Cache info: {info}")
    
    # キャッシュクリア
    cache.clear()
    
    # 再取得（None になるはず）
    retrieved_after_clear = cache.get("test_key")
    print(f"After clear: {retrieved_after_clear}")


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # テスト実行
    test_cache_manager()