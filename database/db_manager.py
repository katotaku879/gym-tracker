# database/db_manager.py
import sqlite3
import logging
from contextlib import contextmanager
from datetime import date, datetime
from typing import List, Optional, Tuple
import shutil
import os

from .models import Exercise, Workout, Set, Goal, BodyStats
from utils.constants import DB_FILE
from utils.calculations import calculate_one_rm

class DatabaseManager:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.logger = logging.getLogger(__name__)
        try:
            self.init_database()
        except Exception as e:
            self.logger.critical(f"Database initialization failed: {e}")
            raise

    def get_connection(self):
        """データベース接続取得"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def safe_transaction(self):
        """安全なトランザクション実行"""
        conn = None
        try:
            conn = self.get_connection()
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Transaction failed: {e}")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Unexpected error in transaction: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """データベース初期化"""
        with self.safe_transaction() as conn:
            # exercisesテーブル作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    variation TEXT NOT NULL,
                    category TEXT NOT NULL
                )
            """)

            # workoutsテーブル作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    notes TEXT
                )
            """)

            # setsテーブル作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER,
                    exercise_id INTEGER,
                    set_number INTEGER,
                    weight REAL NOT NULL,
                    reps INTEGER NOT NULL,
                    one_rm REAL,
                    FOREIGN KEY (workout_id) REFERENCES workouts(id),
                    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
                )
            """)

            # goalsテーブル作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exercise_id INTEGER,
                    target_weight REAL,
                    current_weight REAL,
                    target_month TEXT,
                    achieved BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
                )
            """)

            # body_statsテーブル作成
            conn.execute("""
                CREATE TABLE IF NOT EXISTS body_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    weight REAL,
                    body_fat_percentage REAL,
                    muscle_mass REAL
                )
            """)

            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sets_workout_id ON sets(workout_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sets_exercise_id ON sets(exercise_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(date)")

            # 初期データ挿入
            self._insert_initial_exercises(conn)

    def _insert_initial_exercises(self, conn):
        """初期種目データ挿入"""
        # 既存データチェック
        cursor = conn.execute("SELECT COUNT(*) FROM exercises")
        if cursor.fetchone()[0] > 0:
            return  # 既にデータが存在する場合はスキップ

        exercises_data = [
            # 胸
            ('ベンチプレス', 'バーベル', '胸'),
            ('ベンチプレス', 'ダンベル', '胸'),
            ('ベンチプレス', 'マシン', '胸'),
            ('チェストプレス', 'マシン', '胸'),
            ('ダンベルフライ', 'ダンベル', '胸'),
            ('ペックフライ', 'マシン', '胸'),
            ('ケーブルフライ', 'ケーブル', '胸'),
            ('プッシュアップ', '自重', '胸'),
            # 背中
            ('デッドリフト', 'バーベル', '背中'),
            ('ベントオーバーロウ', 'バーベル', '背中'),
            ('ラットプルダウン', 'マシン', '背中'),
            ('シーテッドロウ', 'マシン', '背中'),
            ('プルアップ', '自重', '背中'),
            ('懸垂', '自重', '背中'),
            # 脚
            ('スクワット', 'バーベル', '脚'),
            ('スクワット', '自重', '脚'),
            ('レッグプレス', 'マシン', '脚'),
            ('レッグカール', 'マシン', '脚'),
            ('レッグエクステンション', 'マシン', '脚'),
            # 肩
            ('ショルダープレス', 'バーベル', '肩'),
            ('ショルダープレス', 'ダンベル', '肩'),
            ('ショルダープレス', 'マシン', '肩'),
            ('サイドレイズ', 'ダンベル', '肩'),
            ('インクラインサイドレイズ', 'ダンベル', '肩'),
            ('リアデルト', 'マシン', '肩'),
            ('フェイスプル', 'ケーブル', '肩'),
            # 腕
            ('バーベルカール', 'バーベル', '腕'),
            ('ダンベルカール', 'ダンベル', '腕'),
            ('インクラインカール', 'ダンベル', '腕'),
            ('インクラインハンマーカール', 'ダンベル', '腕'),
            ('ケーブルカール', 'ケーブル', '腕'),
            ('トライセップスエクステンション', 'ダンベル', '腕'),
            ('フレンチプレス', 'ダンベル', '腕'),
            ('プッシュダウン', 'ケーブル', '腕'),
            ('ディップス', '自重', '腕'),
        ]

        conn.executemany(
            "INSERT INTO exercises (name, variation, category) VALUES (?, ?, ?)",
            exercises_data
        )

    # Exercise CRUD operations
    def get_all_exercises(self) -> List[Exercise]:
        """全種目取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, name, variation, category FROM exercises ORDER BY category, name, variation"
                )
                return [Exercise(*row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get exercises: {e}")
            return []

    def get_exercises_by_category(self, category: str) -> List[Exercise]:
        """カテゴリ別種目取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, name, variation, category FROM exercises WHERE category = ? ORDER BY name, variation",
                    (category,)
                )
                return [Exercise(*row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get exercises by category: {e}")
            return []

    # Workout CRUD operations
    def add_workout(self, workout_date: date, notes: Optional[str] = None) -> Optional[int]:
        """ワークアウト追加"""
        try:
            with self.safe_transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO workouts (date, notes) VALUES (?, ?)",
                    (workout_date, notes)
                )
                workout_id = cursor.lastrowid
                self.logger.info(f"Workout added: ID {workout_id}")
                return workout_id
        except Exception as e:
            self.logger.error(f"Failed to add workout: {e}")
            return None

    def get_workout_by_date(self, workout_date: date) -> Optional[Workout]:
        """日付でワークアウト取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, date, notes FROM workouts WHERE date = ?",
                    (workout_date,)
                )
                row = cursor.fetchone()
                if row:
                    return Workout(*row)
                return None
        except Exception as e:
            self.logger.error(f"Failed to get workout by date: {e}")
            return None

    # Set CRUD operations
    def add_set_safe(self, set_data: Set) -> bool:
        """セット追加（安全版）"""
        try:
            with self.safe_transaction() as conn:
                one_rm = calculate_one_rm(set_data.weight, set_data.reps)
                cursor = conn.execute(
                    """INSERT INTO sets 
                       (workout_id, exercise_id, set_number, weight, reps, one_rm)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (set_data.workout_id, set_data.exercise_id, set_data.set_number,
                     set_data.weight, set_data.reps, one_rm)
                )
                self.logger.info(f"Set added successfully: {cursor.lastrowid}")
                return True
        except sqlite3.IntegrityError:
            self.logger.warning("Duplicate set data attempted")
            return False
        except Exception as e:
            self.logger.error(f"Failed to add set: {e}")
            return False

    def get_last_exercise_record(self, exercise_id: int) -> Optional[List[Set]]:
        """種目の最新記録取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.id, s.workout_id, s.exercise_id, s.set_number, 
                           s.weight, s.reps, s.one_rm
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ?
                    ORDER BY w.date DESC, s.set_number
                    LIMIT 10
                """, (exercise_id,))
                
                rows = cursor.fetchall()
                if rows:
                    return [Set(*row) for row in rows]
                return None
        except Exception as e:
            self.logger.error(f"Failed to get last exercise record: {e}")
            return None

    def get_history_paginated(self, page_size=100, offset=0):
        """ページネーション付き履歴取得"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT w.date, e.name, e.variation, s.set_number,
                           s.weight, s.reps, s.one_rm, s.id
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    JOIN exercises e ON s.exercise_id = e.id
                    ORDER BY w.date DESC, s.id
                    LIMIT ? OFFSET ?
                """
                cursor = conn.execute(query, (page_size, offset))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Paginated history fetch failed: {e}")
            return []

    def get_history_filtered(self, start_date=None, end_date=None, exercise_id=None, page_size=100, offset=0):
        """フィルタ付き履歴取得"""
        try:
            with self.get_connection() as conn:
                # ベースクエリ
                query = """
                    SELECT w.date, e.name, e.variation, s.set_number,
                           s.weight, s.reps, s.one_rm, s.id
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    JOIN exercises e ON s.exercise_id = e.id
                """
                
                # WHERE条件とパラメータ
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("w.date >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("w.date <= ?")
                    params.append(end_date)
                
                if exercise_id:
                    conditions.append("e.id = ?")
                    params.append(exercise_id)
                
                # WHERE句を追加
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # ORDER BY とページネーション
                query += " ORDER BY w.date DESC, s.id LIMIT ? OFFSET ?"
                params.extend([page_size, offset])
                
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Filtered history fetch failed: {e}")
            return []

    def get_filtered_record_count(self, start_date=None, end_date=None, exercise_id=None):
        """フィルタ条件に一致するレコード数を取得"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT COUNT(*)
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    JOIN exercises e ON s.exercise_id = e.id
                """
                
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("w.date >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("w.date <= ?")
                    params.append(end_date)
                
                if exercise_id:
                    conditions.append("e.id = ?")
                    params.append(exercise_id)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                cursor = conn.execute(query, params)
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Filtered record count failed: {e}")
            return 0

    def get_total_record_count(self):
        """総レコード数取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sets")
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Record count fetch failed: {e}")
            return 0

    # Backup and utility methods
    def backup_database(self, backup_dir: str = "backup") -> bool:
        """データベースバックアップ"""
        try:
            if not os.path.exists(self.db_file):
                return True  # ファイルが存在しない場合はOK
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"gym_tracker_backup_{timestamp}.db")
            
            shutil.copy2(self.db_file, backup_file)
            self.logger.info(f"Backup created: {backup_file}")
            return True
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False