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
        
    # database/db_manager.py に追加するメソッド群

    def init_goals_table(self):
        """目標テーブルの初期化（既存のinit_databaseメソッドに追加）"""
        with self.safe_transaction() as conn:
            # goalsテーブル作成（notesカラムを追加）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exercise_id INTEGER,
                    target_weight REAL NOT NULL,
                    current_weight REAL NOT NULL,
                    target_month TEXT NOT NULL,
                    achieved BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
                )
            """)
            
            # インデックス作成
            conn.execute("CREATE INDEX IF NOT EXISTS idx_goals_exercise_id ON goals(exercise_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_goals_achieved ON goals(achieved)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_goals_target_month ON goals(target_month)")

    

    # Goal CRUD operations
    # database/db_manager.py に以下のメソッドを全て追加
# （ファイルの最後、既存のメソッドの後に追加してください）

    # ===========================================
    # 目標管理機能 - 完全版
    # ===========================================
    
    def add_goal(self, goal: Goal) -> Optional[int]:
        """目標追加"""
        try:
            with self.safe_transaction() as conn:
                cursor = conn.execute(
                    """INSERT INTO goals 
                       (exercise_id, target_weight, current_weight, target_month, achieved)
                       VALUES (?, ?, ?, ?, ?)""",
                    (goal.exercise_id, goal.target_weight, goal.current_weight, 
                     goal.target_month, goal.achieved)
                )
                goal_id = cursor.lastrowid
                self.logger.info(f"Goal added successfully: ID {goal_id}")
                return goal_id
        except Exception as e:
            self.logger.error(f"Failed to add goal: {e}")
            return None
    
    def get_all_goals_with_exercise_names(self) -> List[Dict]:
        """全目標と種目名を一緒に取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT g.id, g.exercise_id, g.target_weight, g.current_weight,
                           g.target_month, g.achieved,
                           e.name, e.variation, e.category
                    FROM goals g
                    JOIN exercises e ON g.exercise_id = e.id
                    ORDER BY g.achieved ASC, g.target_month ASC
                """)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'goal': Goal(row[0], row[1], row[2], row[3], row[4], row[5]),
                        'exercise_name': f"{row[6]}（{row[7]}）",
                        'category': row[8]
                    })
                return results
        except Exception as e:
            self.logger.error(f"Failed to get goals with exercise names: {e}")
            return []
    
    def update_goal(self, goal: Goal) -> bool:
        """目標更新"""
        try:
            with self.safe_transaction() as conn:
                cursor = conn.execute(
                    """UPDATE goals 
                       SET exercise_id = ?, target_weight = ?, current_weight = ?,
                           target_month = ?, achieved = ?
                       WHERE id = ?""",
                    (goal.exercise_id, goal.target_weight, goal.current_weight,
                     goal.target_month, goal.achieved, goal.id)
                )
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Goal updated successfully: ID {goal.id}")
                    return True
                else:
                    self.logger.warning(f"Goal not found for update: ID {goal.id}")
                    return False
        except Exception as e:
            self.logger.error(f"Failed to update goal: {e}")
            return False
    
    def delete_goal(self, goal_id: int) -> bool:
        """目標削除"""
        try:
            with self.safe_transaction() as conn:
                cursor = conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Goal deleted successfully: ID {goal_id}")
                    return True
                else:
                    self.logger.warning(f"Goal not found for deletion: ID {goal_id}")
                    return False
        except Exception as e:
            self.logger.error(f"Failed to delete goal: {e}")
            return False
    
    def mark_goal_as_achieved(self, goal_id: int) -> bool:
        """目標を達成済みにマーク"""
        try:
            with self.safe_transaction() as conn:
                cursor = conn.execute(
                    """UPDATE goals 
                       SET current_weight = target_weight, achieved = TRUE
                       WHERE id = ?""",
                    (goal_id,)
                )
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Goal marked as achieved: ID {goal_id}")
                    return True
                else:
                    return False
        except Exception as e:
            self.logger.error(f"Failed to mark goal as achieved: {e}")
            return False
    
    def update_goal_current_weight_from_records(self, goal_id: int) -> bool:
        """記録から目標の現在重量を自動更新"""
        try:
            with self.safe_transaction() as conn:
                # 目標の種目IDを取得
                cursor = conn.execute(
                    "SELECT exercise_id FROM goals WHERE id = ?", (goal_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return False
                
                exercise_id = row[0]
                
                # その種目の最新の最大1RMを取得
                cursor = conn.execute("""
                    SELECT MAX(s.one_rm)
                    FROM sets s
                    JOIN workouts w ON s.workout_id = w.id
                    WHERE s.exercise_id = ? AND s.one_rm IS NOT NULL
                    ORDER BY w.date DESC
                    LIMIT 1
                """, (exercise_id,))
                
                row = cursor.fetchone()
                if row and row[0]:
                    max_one_rm = float(row[0])
                    
                    # 目標の現在重量を更新
                    cursor = conn.execute(
                        "UPDATE goals SET current_weight = ? WHERE id = ?",
                        (max_one_rm, goal_id)
                    )
                    
                    if cursor.rowcount > 0:
                        self.logger.info(f"Goal current weight updated: ID {goal_id}, Weight {max_one_rm}")
                        return True
                
                return False
        except Exception as e:
            self.logger.error(f"Failed to update goal current weight: {e}")
            return False
    
    def get_achievable_goals(self) -> List[Dict]:
        """達成可能な目標を取得（現在重量 >= 目標重量）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT g.id, g.exercise_id, g.target_weight, g.current_weight,
                           g.target_month, g.achieved,
                           e.name, e.variation, e.category
                    FROM goals g
                    JOIN exercises e ON g.exercise_id = e.id
                    WHERE g.achieved = FALSE AND g.current_weight >= g.target_weight
                    ORDER BY g.target_month ASC
                """)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'goal': Goal(row[0], row[1], row[2], row[3], row[4], row[5]),
                        'exercise_name': f"{row[6]}（{row[7]}）",
                        'category': row[8]
                    })
                return results
        except Exception as e:
            self.logger.error(f"Failed to get achievable goals: {e}")
            return []
    
    # ===========================================
    # 統計・分析機能（将来の拡張用）
    # ===========================================
    
    def get_goals_by_status(self, achieved: bool = False) -> List[Dict]:
        """ステータス別目標取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT g.id, g.exercise_id, g.target_weight, g.current_weight,
                           g.target_month, g.achieved,
                           e.name, e.variation, e.category
                    FROM goals g
                    JOIN exercises e ON g.exercise_id = e.id
                    WHERE g.achieved = ?
                    ORDER BY g.target_month ASC
                """)
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'goal': Goal(row[0], row[1], row[2], row[3], row[4], row[5]),
                        'exercise_name': f"{row[6]}（{row[7]}）",
                        'category': row[8]
                    })
                return results
        except Exception as e:
            self.logger.error(f"Failed to get goals by status: {e}")
            return []
    
    def get_goals_summary(self) -> Dict[str, int]:
        """目標統計サマリー取得"""
        try:
            with self.get_connection() as conn:
                # 総目標数
                cursor = conn.execute("SELECT COUNT(*) FROM goals")
                total_goals = cursor.fetchone()[0]
                
                # 達成済み目標数
                cursor = conn.execute("SELECT COUNT(*) FROM goals WHERE achieved = 1")
                achieved_goals = cursor.fetchone()[0]
                
                # 今月期限の目標数
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM goals 
                    WHERE strftime('%Y-%m', target_month || '-01') = strftime('%Y-%m', 'now')
                    AND achieved = 0
                """)
                this_month_goals = cursor.fetchone()[0]
                
                # 期限切れ目標数
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM goals 
                    WHERE date(target_month || '-01') < date('now')
                    AND achieved = 0
                """)
                overdue_goals = cursor.fetchone()[0]
                
                return {
                    'total': total_goals,
                    'achieved': achieved_goals,
                    'active': total_goals - achieved_goals,
                    'this_month': this_month_goals,
                    'overdue': overdue_goals,
                    'achievement_rate': int((achieved_goals / total_goals * 100)) if total_goals > 0 else 0
                }
        except Exception as e:
            self.logger.error(f"Failed to get goals summary: {e}")
            return {'total': 0, 'achieved': 0, 'active': 0, 'this_month': 0, 'overdue': 0, 'achievement_rate': 0}
    
    def update_goal_progress_from_recent_records(self) -> int:
        """最新のトレーニング記録から全目標の現在重量を自動更新"""
        try:
            with self.safe_transaction() as conn:
                # 各目標について最新の1RMを取得
                cursor = conn.execute("""
                    SELECT g.id, g.exercise_id, g.current_weight
                    FROM goals g
                    WHERE g.achieved = 0
                """)
                
                goals_to_update = cursor.fetchall()
                update_count = 0
                
                for goal_id, exercise_id, current_weight in goals_to_update:
                    # その種目の最新の最大1RMを取得
                    cursor = conn.execute("""
                        SELECT MAX(s.one_rm)
                        FROM sets s
                        JOIN workouts w ON s.workout_id = w.id
                        WHERE s.exercise_id = ? AND s.one_rm IS NOT NULL
                    """, (exercise_id,))
                    
                    row = cursor.fetchone()
                    if row and row[0] and float(row[0]) > current_weight:
                        latest_one_rm = float(row[0])
                        
                        # 目標の現在重量を更新
                        conn.execute("""
                            UPDATE goals 
                            SET current_weight = ?
                            WHERE id = ?
                        """, (latest_one_rm, goal_id))
                        update_count += 1
                
                if update_count > 0:
                    self.logger.info(f"Updated {update_count} goals with latest progress")
                    
                return update_count
        except Exception as e:
            self.logger.error(f"Failed to update goal progress: {e}")
            return 0

    # database/db_manager.py に以下のメソッドを追加
# （目標管理メソッドの後に追加してください）

    # ===========================================
    # 体組成管理機能
    # ===========================================
    
    # database/db_manager.py に追加するメソッド

    def add_body_stats(self, body_stats: BodyStats) -> Optional[int]:
        """体組成データ追加"""
        try:
            with self.safe_transaction() as conn:
                cursor = conn.execute(
                    """INSERT INTO body_stats (date, weight, body_fat_percentage, muscle_mass)
                    VALUES (?, ?, ?, ?)""",
                    (body_stats.date, body_stats.weight, 
                    body_stats.body_fat_percentage, body_stats.muscle_mass)
                )
                body_stats_id = cursor.lastrowid
                self.logger.info(f"Body stats added: ID {body_stats_id}")
                return body_stats_id
        except Exception as e:
            self.logger.error(f"Failed to add body stats: {e}")
            return None

    def get_all_body_stats(self) -> List[BodyStats]:
        """全体組成データ取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, date, weight, body_fat_percentage, muscle_mass FROM body_stats ORDER BY date DESC"
                )
                return [BodyStats(*row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get body stats: {e}")
            return []

    def get_body_stats_by_date(self, target_date: date) -> Optional[BodyStats]:
        """日付で体組成データ取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, date, weight, body_fat_percentage, muscle_mass FROM body_stats WHERE date = ?",
                    (target_date,)
                )
                row = cursor.fetchone()
                if row:
                    return BodyStats(*row)
                return None
        except Exception as e:
            self.logger.error(f"Failed to get body stats by date: {e}")
            return None

    def update_body_stats(self, body_stats: BodyStats) -> bool:
        """体組成データ更新"""
        try:
            with self.safe_transaction() as conn:
                conn.execute(
                    """UPDATE body_stats 
                    SET date = ?, weight = ?, body_fat_percentage = ?, muscle_mass = ?
                    WHERE id = ?""",
                    (body_stats.date, body_stats.weight, 
                    body_stats.body_fat_percentage, body_stats.muscle_mass, body_stats.id)
                )
                self.logger.info(f"Body stats updated: ID {body_stats.id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to update body stats: {e}")
            return False

    def delete_body_stats(self, body_stats_id: int) -> bool:
        """体組成データ削除"""
        try:
            with self.safe_transaction() as conn:
                conn.execute("DELETE FROM body_stats WHERE id = ?", (body_stats_id,))
                self.logger.info(f"Body stats deleted: ID {body_stats_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete body stats: {e}")
            return False

    def get_body_stats_by_date_range(self, start_date: date, end_date: date) -> List[BodyStats]:
        """期間指定で体組成データ取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """SELECT id, date, weight, body_fat_percentage, muscle_mass 
                    FROM body_stats 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date""",
                    (start_date, end_date)
                )
                return [BodyStats(*row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get body stats by date range: {e}")
            return []

    def get_body_stats_summary(self) -> Dict[str, float]:
        """体組成サマリー取得"""
        try:
            with self.get_connection() as conn:
                # 最新データ
                cursor = conn.execute(
                    """SELECT weight, body_fat_percentage, muscle_mass 
                    FROM body_stats 
                    ORDER BY date DESC LIMIT 1"""
                )
                latest = cursor.fetchone()
                
                # 1ヶ月前データ
                cursor = conn.execute(
                    """SELECT weight, body_fat_percentage, muscle_mass 
                    FROM body_stats 
                    WHERE date <= date('now', '-1 month')
                    ORDER BY date DESC LIMIT 1"""
                )
                month_ago = cursor.fetchone()
                
                summary = {}
                if latest:
                    summary['current_weight'] = latest[0]
                    summary['current_body_fat'] = latest[1]
                    summary['current_muscle'] = latest[2]
                    
                    if month_ago:
                        summary['weight_change_month'] = (latest[0] or 0) - (month_ago[0] or 0)
                        summary['body_fat_change_month'] = (latest[1] or 0) - (month_ago[1] or 0)
                        summary['muscle_change_month'] = (latest[2] or 0) - (month_ago[2] or 0)
                
                return summary
        except Exception as e:
            self.logger.error(f"Failed to get body stats summary: {e}")
            return {}
        
    # database/db_manager.py に追加するメソッド群

# 既存のDatabaseManagerクラスに以下のメソッドを追加してください

def get_body_stats_optimized(self) -> List[BodyStats]:
    """体組成データ取得（最適化版）"""
    try:
        with self.get_connection() as conn:
            # インデックスを活用した高速クエリ
            cursor = conn.execute("""
                SELECT id, date, weight, body_fat_percentage, muscle_mass 
                FROM body_stats 
                ORDER BY date DESC
                LIMIT 1000
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append(BodyStats(
                    id=row[0],
                    date=row[1],  # SQLiteから直接date型で取得
                    weight=row[2],
                    body_fat_percentage=row[3],
                    muscle_mass=row[4]
                ))
            
            return results
            
    except Exception as e:
        self.logger.error(f"Optimized body stats fetch failed: {e}")
        return []

    def get_body_stats_summary_optimized(self) -> Dict[str, float]:
        """体組成サマリー取得（最適化版）"""
        try:
            with self.get_connection() as conn:
                summary = {}
                
                # 単一のクエリで最新データと前月データを取得
                cursor = conn.execute("""
                    WITH latest_data AS (
                        SELECT weight, body_fat_percentage, muscle_mass, date
                        FROM body_stats 
                        ORDER BY date DESC 
                        LIMIT 1
                    ),
                    month_ago_data AS (
                        SELECT weight, body_fat_percentage, muscle_mass
                        FROM body_stats 
                        WHERE date <= date('now', '-1 month')
                        ORDER BY date DESC
                        LIMIT 1
                    )
                    SELECT 
                        l.weight as current_weight,
                        l.body_fat_percentage as current_body_fat,
                        l.muscle_mass as current_muscle,
                        m.weight as month_ago_weight,
                        m.body_fat_percentage as month_ago_body_fat,
                        m.muscle_mass as month_ago_muscle
                    FROM latest_data l
                    LEFT JOIN month_ago_data m ON 1=1
                """)
                
                row = cursor.fetchone()
                if row:
                    # 現在の値
                    if row[0] is not None:
                        summary['current_weight'] = float(row[0])
                    if row[1] is not None:
                        summary['current_body_fat'] = float(row[1])
                    if row[2] is not None:
                        summary['current_muscle'] = float(row[2])
                    
                    # 変化量計算
                    if row[0] is not None and row[3] is not None:
                        summary['weight_change_month'] = float(row[0]) - float(row[3])
                    if row[1] is not None and row[4] is not None:
                        summary['body_fat_change_month'] = float(row[1]) - float(row[4])
                    if row[2] is not None and row[5] is not None:
                        summary['muscle_change_month'] = float(row[2]) - float(row[5])
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Optimized summary fetch failed: {e}")
            return {}

    def get_body_stats_by_date_range_optimized(self, start_date: date, end_date: date) -> List[BodyStats]:
        """期間指定で体組成データ取得（最適化版）"""
        try:
            with self.get_connection() as conn:
                # パラメータ化クエリ + インデックス活用
                cursor = conn.execute("""
                    SELECT id, date, weight, body_fat_percentage, muscle_mass 
                    FROM body_stats 
                    WHERE date >= ? AND date <= ?
                    ORDER BY date DESC
                """, (start_date, end_date))
                
                results = []
                for row in cursor.fetchall():
                    results.append(BodyStats(
                        id=row[0],
                        date=row[1],
                        weight=row[2],
                        body_fat_percentage=row[3],
                        muscle_mass=row[4]
                    ))
                
                return results
                
        except Exception as e:
            self.logger.error(f"Optimized date range fetch failed: {e}")
            return []

    def get_latest_body_stats(self, limit: int = 10) -> List[BodyStats]:
        """最新の体組成データ取得（高速版）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, date, weight, body_fat_percentage, muscle_mass 
                    FROM body_stats 
                    ORDER BY date DESC
                    LIMIT ?
                """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append(BodyStats(
                        id=row[0],
                        date=row[1],
                        weight=row[2],
                        body_fat_percentage=row[3],
                        muscle_mass=row[4]
                    ))
                
                return results
                
        except Exception as e:
            self.logger.error(f"Latest body stats fetch failed: {e}")
            return []

    def ensure_body_stats_indexes(self):
        """体組成データ用インデックス作成"""
        try:
            with self.safe_transaction() as conn:
                # 日付インデックス（降順）
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_body_stats_date_desc 
                    ON body_stats(date DESC)
                """)
                
                # 複合インデックス（日付＋重量）
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_body_stats_date_weight 
                    ON body_stats(date DESC, weight)
                """)
                
                self.logger.info("Body stats indexes ensured")
                
        except Exception as e:
            self.logger.error(f"Index creation failed: {e}")

    def optimize_database(self):
        """データベース最適化"""
        try:
            with self.safe_transaction() as conn:
                # VACUUM（データベース最適化）
                conn.execute("VACUUM")
                
                # ANALYZE（統計情報更新）
                conn.execute("ANALYZE")
                
                # 体組成テーブルのインデックス確保
                self.ensure_body_stats_indexes()
                
                self.logger.info("Database optimization completed")
                return True
                
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            return False

    def get_body_stats_count(self) -> int:
        """体組成データ件数取得（高速版）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM body_stats")
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Body stats count failed: {e}")
            return 0

    # 既存メソッドの最適化版への置き換え（オプション）
    def get_all_body_stats_fast(self) -> List[BodyStats]:
        """全体組成データ取得（高速版）- 既存メソッドの代替"""
        return self.get_body_stats_optimized()

    def get_body_stats_summary_fast(self) -> Dict[str, float]:
        """体組成サマリー取得（高速版）- 既存メソッドの代替"""
        return self.get_body_stats_summary_optimized()

    # init_database メソッドに追加するコード（既存のinit_database内に追加）
    def init_database_body_stats_optimization(self):
        """init_database メソッド内に追加するコード"""
        
        # body_statsテーブル作成（既存コードの後に追加）
        with self.safe_transaction() as conn:
            # パフォーマンス最適化のための設定
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous = NORMAL")  # 高速化
            conn.execute("PRAGMA cache_size = 10000")   # キャッシュサイズ増加
            conn.execute("PRAGMA temp_store = MEMORY")  # 一時データをメモリに
            
            # インデックス作成
            self.ensure_body_stats_indexes()

    # 使用例とテスト
    def test_optimized_methods(self):
        """最適化メソッドのテスト"""
        try:
            # データ取得テスト
            stats = self.get_body_stats_optimized()
            print(f"取得データ数: {len(stats)}")
            
            # サマリーテスト
            summary = self.get_body_stats_summary_optimized()
            print(f"サマリー: {summary}")
            
            # データベース最適化テスト
            result = self.optimize_database()
            print(f"最適化結果: {result}")
            
            return True
        except Exception as e:
            print(f"テスト失敗: {e}")
            return False    

# database/models.py のGoalクラスも拡張
        @dataclass
        class Goal:
            """目標モデル - 拡張版"""
            id: Optional[int]
            exercise_id: int
            target_weight: float
            current_weight: float
            target_month: str  # YYYY-MM-DD
            achieved: bool = False
            notes: Optional[str] = None
            created_at: Optional[str] = None
            updated_at: Optional[str] = None
            
            def progress_percentage(self) -> int:
                """進捗率計算"""
                if self.target_weight <= 0:
                    return 0
                return min(int((self.current_weight / self.target_weight) * 100), 100)
            
            def remaining_weight(self) -> float:
                """残り重量計算"""
                return max(0, self.target_weight - self.current_weight)
            
            def is_overdue(self) -> bool:
                """期限切れ判定"""
                try:
                    from datetime import datetime, date
                    target_date = datetime.strptime(self.target_month, '%Y-%m-%d').date()
                    return target_date < date.today() and not self.achieved
                except:
                    return False
            
            def days_remaining(self) -> Optional[int]:
                """残り日数計算"""
                try:
                    from datetime import datetime, date
                    target_date = datetime.strptime(self.target_month, '%Y-%m-%d').date()
                    today = date.today()
                    delta = (target_date - today).days
                    return max(0, delta)
                except:
                    return None    