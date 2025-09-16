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
from typing import List, Dict, Optional, Tuple

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
        
    # database/db_manager.py に追加するメソッド群
# 既存のファイルの末尾に以下のメソッドを追加してください

    def backup_database(self) -> bool:
        """データベースバックアップ作成"""
        try:
            import shutil
            import os
            from datetime import datetime
            
            # backupディレクトリ作成
            backup_dir = "backup"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # バックアップファイル名（タイムスタンプ付き）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"gym_tracker_backup_{timestamp}.db")
            
            # ファイルコピー
            shutil.copy2(self.db_file, backup_file)
            
            self.logger.info(f"Database backup created: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False
    
    def get_best_records(self) -> List[Dict]:
        """ベスト記録取得（統計タブ用）"""
        try:
            with self.get_connection() as conn:
                query = """
                SELECT 
                    e.name || '（' || e.variation || '）' as exercise_name,
                    MAX(s.weight) as max_weight,
                    MAX(s.reps) as max_reps,
                    MAX(s.one_rm) as max_one_rm
                FROM sets s
                JOIN exercises e ON s.exercise_id = e.id
                GROUP BY s.exercise_id
                HAVING COUNT(s.id) > 0
                ORDER BY max_one_rm DESC
                LIMIT 10
                """
                cursor = conn.execute(query)
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get best records: {e}")
            return []
    
    def get_workout_statistics(self) -> Dict[str, float]:
        """ワークアウト統計取得（統計タブ用）"""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # 総ワークアウト数
                cursor = conn.execute("SELECT COUNT(DISTINCT id) FROM workouts")
                result = cursor.fetchone()
                stats['total_workouts'] = result[0] if result else 0
                
                # 総セット数
                cursor = conn.execute("SELECT COUNT(*) FROM sets")
                result = cursor.fetchone()
                stats['total_sets'] = result[0] if result else 0
                
                # 平均セット数/ワークアウト
                if stats['total_workouts'] > 0:
                    stats['avg_sets_per_workout'] = stats['total_sets'] / stats['total_workouts']
                else:
                    stats['avg_sets_per_workout'] = 0
                
                # 連続トレーニング日数計算
                stats['current_streak'] = self._calculate_current_streak(conn)
                stats['max_streak'] = self._calculate_max_streak(conn)
                
                # 今月のトレーニング日数
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT date) 
                    FROM workouts 
                    WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                """)
                result = cursor.fetchone()
                stats['this_month_workouts'] = result[0] if result else 0
                
                # 平均重量
                cursor = conn.execute("SELECT AVG(weight) FROM sets WHERE weight > 0")
                result = cursor.fetchone()
                stats['avg_weight'] = result[0] if result and result[0] else 0
                
                # 総重量（重量×回数）
                cursor = conn.execute("SELECT SUM(weight * reps) FROM sets")
                result = cursor.fetchone()
                stats['total_volume'] = result[0] if result and result[0] else 0
                
                return stats
        except Exception as e:
            self.logger.error(f"Workout statistics fetch failed: {e}")
            return {
                'total_workouts': 0, 'total_sets': 0, 'avg_sets_per_workout': 0,
                'current_streak': 0, 'max_streak': 0, 'this_month_workouts': 0,
                'avg_weight': 0, 'total_volume': 0
            }
    
    def _calculate_current_streak(self, conn) -> int:
        """現在の連続トレーニング日数計算"""
        try:
            cursor = conn.execute("""
                SELECT DISTINCT date 
                FROM workouts 
                ORDER BY date DESC
                LIMIT 30
            """)
            dates = [row[0] for row in cursor.fetchall()]
            
            if not dates:
                return 0
            
            from datetime import datetime, timedelta, date
            today = date.today()
            streak = 0
            current_date = today
            
            for date_str in dates:
                workout_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                if workout_date == current_date or workout_date == current_date - timedelta(days=1):
                    streak += 1
                    current_date = workout_date - timedelta(days=1)
                else:
                    break
            
            return streak
        except Exception as e:
            self.logger.error(f"Current streak calculation failed: {e}")
            return 0
    
    def _calculate_max_streak(self, conn) -> int:
        """最長連続日数計算"""
        try:
            cursor = conn.execute("""
                SELECT DISTINCT date 
                FROM workouts 
                ORDER BY date
            """)
            dates = [row[0] for row in cursor.fetchall()]
            
            if not dates:
                return 0
            
            from datetime import datetime, timedelta
            max_streak = 1
            current_streak = 1
            
            for i in range(1, len(dates)):
                prev_date = datetime.strptime(dates[i-1], '%Y-%m-%d').date()
                curr_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
                
                if curr_date == prev_date + timedelta(days=1):
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
            
            return max_streak
        except Exception as e:
            self.logger.error(f"Max streak calculation failed: {e}")
            return 0
    
    def get_one_rm_progress(self, exercise_id: int, period_days: int) -> List[Dict]:
        """1RM推移データ取得"""
        try:
            with self.get_connection() as conn:
                if period_days > 0:
                    query = """
                    SELECT 
                        w.date,
                        MAX(s.one_rm) as one_rm
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ? AND w.date >= date('now', '-{} days')
                    GROUP BY w.date
                    ORDER BY w.date
                    """.format(period_days)
                else:
                    query = """
                    SELECT 
                        w.date,
                        MAX(s.one_rm) as one_rm
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ?
                    GROUP BY w.date
                    ORDER BY w.date
                    """
                cursor = conn.execute(query, (exercise_id,))
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"1RM progress fetch failed: {e}")
            return []
    
    def get_weight_progress(self, exercise_id: int, period_days: int) -> List[Dict]:
        """重量推移データ取得"""
        try:
            with self.get_connection() as conn:
                if period_days > 0:
                    query = """
                    SELECT 
                        w.date,
                        MAX(s.weight) as max_weight,
                        AVG(s.weight) as avg_weight
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ? AND w.date >= date('now', '-{} days')
                    GROUP BY w.date
                    ORDER BY w.date
                    """.format(period_days)
                else:
                    query = """
                    SELECT 
                        w.date,
                        MAX(s.weight) as max_weight,
                        AVG(s.weight) as avg_weight
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ?
                    GROUP BY w.date
                    ORDER BY w.date
                    """
                cursor = conn.execute(query, (exercise_id,))
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Weight progress fetch failed: {e}")
            return []
    
    def get_volume_progress(self, exercise_id: int, period_days: int) -> List[Dict]:
        """ボリューム推移データ取得"""
        try:
            with self.get_connection() as conn:
                if period_days > 0:
                    query = """
                    SELECT 
                        w.date,
                        SUM(s.weight * s.reps) as total_volume
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ? AND w.date >= date('now', '-{} days')
                    GROUP BY w.date
                    ORDER BY w.date
                    """.format(period_days)
                else:
                    query = """
                    SELECT 
                        w.date,
                        SUM(s.weight * s.reps) as total_volume
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ?
                    GROUP BY w.date
                    ORDER BY w.date
                    """
                cursor = conn.execute(query, (exercise_id,))
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Volume progress fetch failed: {e}")
            return []
    
    def get_frequency_analysis(self, period_days: int) -> List[Dict]:
        """頻度分析データ取得"""
        try:
            with self.get_connection() as conn:
                if period_days > 0:
                    query = """
                    SELECT 
                        CASE strftime('%w', w.date)
                            WHEN '0' THEN 6  -- 日曜日を6に
                            WHEN '1' THEN 0  -- 月曜日を0に
                            WHEN '2' THEN 1  -- 火曜日を1に
                            WHEN '3' THEN 2  -- 水曜日を2に
                            WHEN '4' THEN 3  -- 木曜日を3に
                            WHEN '5' THEN 4  -- 金曜日を4に
                            WHEN '6' THEN 5  -- 土曜日を5に
                        END as day_of_week,
                        COUNT(DISTINCT w.date) as count
                    FROM workouts w
                    WHERE w.date >= date('now', '-{} days')
                    GROUP BY day_of_week
                    ORDER BY day_of_week
                    """.format(period_days)
                else:
                    query = """
                    SELECT 
                        CASE strftime('%w', w.date)
                            WHEN '0' THEN 6  -- 日曜日を6に
                            WHEN '1' THEN 0  -- 月曜日を0に
                            WHEN '2' THEN 1  -- 火曜日を1に
                            WHEN '3' THEN 2  -- 水曜日を2に
                            WHEN '4' THEN 3  -- 木曜日を3に
                            WHEN '5' THEN 4  -- 金曜日を4に
                            WHEN '6' THEN 5  -- 土曜日を5に
                        END as day_of_week,
                        COUNT(DISTINCT w.date) as count
                    FROM workouts w
                    GROUP BY day_of_week
                    ORDER BY day_of_week
                    """
                cursor = conn.execute(query)
                results = cursor.fetchall()
                
                # 7日分のデータを作成（0件の曜日も含める）
                week_data = [0] * 7
                for row in results:
                    day_index = row[0]
                    count = row[1]
                    if day_index is not None:
                        week_data[day_index] = count
                
                return [{'day': i, 'count': count} for i, count in enumerate(week_data)]
        except Exception as e:
            self.logger.error(f"Frequency analysis fetch failed: {e}")
            return [{'day': i, 'count': 0} for i in range(7)]
    
    def get_category_analysis(self, period_days: int) -> List[Dict]:
        """部位別分析データ取得"""
        try:
            with self.get_connection() as conn:
                if period_days > 0:
                    query = """
                    SELECT 
                        e.category,
                        COUNT(s.id) as count
                    FROM sets s
                    JOIN exercises e ON s.exercise_id = e.id
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE w.date >= date('now', '-{} days')
                    GROUP BY e.category
                    ORDER BY count DESC
                    """.format(period_days)
                else:
                    query = """
                    SELECT 
                        e.category,
                        COUNT(s.id) as count
                    FROM sets s
                    JOIN exercises e ON s.exercise_id = e.id
                    JOIN workouts w ON s.workout_id = w.id
                    GROUP BY e.category
                    ORDER BY count DESC
                    """
                cursor = conn.execute(query)
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Category analysis fetch failed: {e}")
            return []  