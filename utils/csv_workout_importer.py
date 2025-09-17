# utils/csv_workout_importer.py
"""
CSVファイルからワークアウトデータをインポートする機能
バーベルスクワットなどの重量・回数・1RMデータを取り込み
"""

import csv
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
import logging
import os
import re
from database.models import Workout, Set, Exercise
from database.db_manager import DatabaseManager

class CSVWorkoutImporter:
    """CSVワークアウトデータインポートクラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def import_workout_csv(self, csv_path: str, exercise_name: Optional[str] = None, 
                          exercise_variation: Optional[str] = None, exercise_category: Optional[str] = None,
                          overwrite: bool = False) -> Dict[str, int]:
        """
        CSVファイルからワークアウトデータをインポート
        
        Args:
            csv_path: CSVファイルのパス
            exercise_name: 種目名（例：'スクワット'）
            exercise_variation: バリエーション（例：'バーベル'）
            exercise_category: カテゴリ（例：'脚'）
            overwrite: 既存データの上書き許可
            
        Returns:
            インポート結果の辞書
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")
        
        try:
            # ファイル名から種目情報を自動推測
            if not exercise_name:
                exercise_info = self._extract_exercise_from_filename(csv_path)
                exercise_name = exercise_info.get('name', 'スクワット')
                exercise_variation = exercise_info.get('variation', 'バーベル')
                exercise_category = exercise_info.get('category', '脚')
            
            # None チェック
            if not exercise_name or not exercise_variation or not exercise_category:
                raise ValueError("種目情報が不完全です")
            
            self.logger.info(f"CSVインポート開始: {csv_path}")
            self.logger.info(f"種目: {exercise_name} ({exercise_variation}) - {exercise_category}")
            
            # CSVファイル読み込み
            workout_data = self._read_csv_file(csv_path)
            
            # 種目IDを取得または作成
            exercise_id = self._get_or_create_exercise(
                exercise_name, exercise_variation, exercise_category
            )
            
            if exercise_id is None:
                raise ValueError("種目IDの取得に失敗しました")
            
            # データベースにインポート
            import_result = self._import_to_database(workout_data, exercise_id, overwrite)
            
            self.logger.info(f"CSVインポート完了: {import_result}")
            return import_result
            
        except Exception as e:
            self.logger.error(f"CSVインポートエラー: {e}")
            raise
    
    def _extract_exercise_from_filename(self, csv_path: str) -> Dict[str, str]:
        """ファイル名から種目情報を推測"""
        filename = os.path.basename(csv_path).lower()
        
        # 種目マッピング
        exercise_mapping = {
            'squat': {'name': 'スクワット', 'variation': 'バーベル', 'category': '脚'},
            'スクワット': {'name': 'スクワット', 'variation': 'バーベル', 'category': '脚'},
            'バーベルスクワット': {'name': 'スクワット', 'variation': 'バーベル', 'category': '脚'},
            'bench': {'name': 'ベンチプレス', 'variation': 'バーベル', 'category': '胸'},
            'ベンチプレス': {'name': 'ベンチプレス', 'variation': 'バーベル', 'category': '胸'},
            'deadlift': {'name': 'デッドリフト', 'variation': 'バーベル', 'category': '背中'},
            'デッドリフト': {'name': 'デッドリフト', 'variation': 'バーベル', 'category': '背中'},
        }
        
        for key, info in exercise_mapping.items():
            if key in filename:
                return info
        
        # デフォルト（スクワットと仮定）
        return {'name': 'スクワット', 'variation': 'バーベル', 'category': '脚'}
    
    def _read_csv_file(self, csv_path: str) -> List[Dict]:
        """CSVファイル読み込みと解析"""
        try:
            # pandasで読み込み（エンコーディング自動判定）
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # 列名をクリーニング
            df.columns = df.columns.str.strip()
            
            self.logger.info(f"CSV読み込み成功: {len(df)}行, 列: {list(df.columns)}")
            
            # データをパース
            workout_records = []
            for row_idx, (_, row) in enumerate(df.iterrows()):
                try:
                    record = self._parse_workout_row(row, row_idx)
                    if record:
                        workout_records.append(record)
                except Exception as e:
                    self.logger.warning(f"行 {row_idx + 2} のパースに失敗: {e}")
                    continue
            
            return workout_records
            
        except Exception as e:
            # エンコーディングエラーの場合、他のエンコーディングを試行
            try:
                df = pd.read_csv(csv_path, encoding='shift_jis')
                df.columns = df.columns.str.strip()
                
                workout_records = []
                for row_idx, (_, row) in enumerate(df.iterrows()):
                    try:
                        record = self._parse_workout_row(row, row_idx)
                        if record:
                            workout_records.append(record)
                    except Exception as e:
                        self.logger.warning(f"行 {row_idx + 2} のパースに失敗: {e}")
                        continue
                
                return workout_records
                
            except Exception:
                raise ValueError(f"CSVファイル読み込みエラー: {e}")
    
    def _parse_workout_row(self, row: pd.Series, row_index: int) -> Optional[Dict]:
        """CSV行をワークアウトデータに変換"""
        try:
            # 日付パース
            date_str = str(row.get('Date', '')).strip()
            if not date_str or date_str == 'nan':
                return None
            
            workout_date = self._parse_date(date_str)
            if not workout_date:
                return None
            
            # セットデータを抽出
            sets_data = []
            for set_num in range(1, 6):  # 最大5セット
                weight_col = f'{set_num} Set [WT]'
                reps_col = f'{set_num} Set [Reps]'
                orm_col = f'{set_num} Set [1RM]'
                
                weight = row.get(weight_col)
                reps = row.get(reps_col)
                one_rm = row.get(orm_col)
                
                # 重量と回数が両方ある場合のみセットとして追加
                if pd.notna(weight) and pd.notna(reps) and weight > 0 and reps > 0:
                    # 1RMが記録されていない場合は計算
                    if pd.isna(one_rm) or one_rm <= 0:
                        one_rm = self._calculate_one_rm(float(weight), int(reps))
                    
                    sets_data.append({
                        'set_number': set_num,
                        'weight': float(weight),
                        'reps': int(reps),
                        'one_rm': float(one_rm)
                    })
            
            if not sets_data:
                return None
            
            return {
                'date': workout_date,
                'sets': sets_data,
                'total_volume': row.get('Total (kg)', 0),
                'max_1rm': row.get('1RM (kg)', 0),
                'max_weight': row.get('Max (kg)', 0)
            }
            
        except Exception as e:
            self.logger.warning(f"行パースエラー: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """日付文字列をdateオブジェクトに変換"""
        date_formats = [
            '%Y/%m/%d',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y年%m月%d日'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        self.logger.warning(f"日付パースに失敗: {date_str}")
        return None
    
    def _calculate_one_rm(self, weight: float, reps: int) -> float:
        """1RM計算（Epley式）"""
        if reps == 1:
            return weight
        return weight * (1 + reps / 30.0)
    
    def _get_or_create_exercise(self, name: str, variation: str, category: str) -> Optional[int]:
        """種目を取得または新規作成"""
        try:
            # 既存の種目を検索
            exercises = self.db_manager.get_all_exercises()
            for exercise in exercises:
                if (exercise.name == name and 
                    exercise.variation == variation and 
                    exercise.category == category):
                    return exercise.id
            
            # 種目が存在しない場合は新規作成
            with self.db_manager.safe_transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO exercises (name, variation, category) VALUES (?, ?, ?)",
                    (name, variation, category)
                )
                exercise_id = cursor.lastrowid
                
                if exercise_id:
                    self.logger.info(f"新しい種目を作成: {name} ({variation}) - {category}")
                    return exercise_id
                else:
                    self.logger.error("種目の作成に失敗しました")
                    return None
                    
        except Exception as e:
            self.logger.error(f"種目取得・作成エラー: {e}")
            return None
    
    def _import_to_database(self, workout_data: List[Dict], exercise_id: int, 
                           overwrite: bool) -> Dict[str, int]:
        """データベースにワークアウトデータをインポート"""
        imported_workouts = 0
        imported_sets = 0
        skipped_workouts = 0
        
        try:
            for workout_record in workout_data:
                workout_date = workout_record['date']
                sets_data = workout_record['sets']
                
                # 既存のワークアウトをチェック
                existing_workout = self._find_existing_workout(workout_date, exercise_id)
                
                if existing_workout and not overwrite:
                    skipped_workouts += 1
                    self.logger.info(f"スキップ（既存）: {workout_date}")
                    continue
                
                # ワークアウト作成または取得
                if existing_workout and overwrite:
                    workout_id = existing_workout.id
                    if workout_id is not None:
                        # 既存のセットを削除
                        self._delete_existing_sets(workout_id, exercise_id)
                else:
                    # 新しいワークアウトを作成
                    workout_id = self.db_manager.add_workout(
                        workout_date, f"CSVインポート - {exercise_id}"
                    )
                    if not workout_id:
                        continue
                
                # セットデータを追加
                for set_data in sets_data:
                    with self.db_manager.safe_transaction() as conn:
                        cursor = conn.execute("""
                            INSERT INTO sets (workout_id, exercise_id, set_number, weight, reps, one_rm)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (workout_id, exercise_id, set_data['set_number'], 
                            set_data['weight'], set_data['reps'], set_data['one_rm']))
                        
                        if cursor.lastrowid:
                            imported_sets += 1
                
                imported_workouts += 1
                self.logger.info(f"インポート完了: {workout_date} - {len(sets_data)}セット")
            
            return {
                'imported_workouts': imported_workouts,
                'imported_sets': imported_sets,
                'skipped_workouts': skipped_workouts,
                'total_records': len(workout_data)
            }
            
        except Exception as e:
            self.logger.error(f"データベースインポートエラー: {e}")
            raise
    
    def _find_existing_workout(self, workout_date: date, exercise_id: int) -> Optional[Workout]:
        """既存のワークアウトを検索"""
        try:
            # その日の既存ワークアウトを検索
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT w.id, w.date, w.notes
                    FROM workouts w
                    JOIN sets s ON w.id = s.workout_id
                    WHERE w.date = ? AND s.exercise_id = ?
                """, (workout_date, exercise_id))
                
                row = cursor.fetchone()
                if row:
                    return Workout(id=row[0], date=row[1], notes=row[2])
                return None
                
        except Exception as e:
            self.logger.warning(f"既存ワークアウト検索エラー: {e}")
            return None
    
    def _delete_existing_sets(self, workout_id: int, exercise_id: int):
        """既存のセットを削除（上書き用）"""
        try:
            with self.db_manager.safe_transaction() as conn:
                conn.execute("""
                    DELETE FROM sets 
                    WHERE workout_id = ? AND exercise_id = ?
                """, (workout_id, exercise_id))
                
        except Exception as e:
            self.logger.error(f"既存セット削除エラー: {e}")
            raise

    def validate_csv_format(self, csv_path: str) -> Dict[str, Any]:
        """CSVファイルの形式を検証"""
        try:
            df = pd.read_csv(csv_path, nrows=5)  # 最初の5行だけ読み込み
            
            required_columns = ['Date']
            set_columns = []
            
            # セット列をチェック
            for i in range(1, 6):
                weight_col = f'{i} Set [WT]'
                reps_col = f'{i} Set [Reps]'
                if weight_col in df.columns and reps_col in df.columns:
                    set_columns.append(i)
            
            return {
                'valid': len(set_columns) > 0 and 'Date' in df.columns,
                'columns': list(df.columns),
                'detected_sets': set_columns,
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'columns': [],
                'detected_sets': [],
                'sample_data': []
            }