# utils/excel_body_stats_importer.py
"""
Excelファイルからの体組成データ一括インポート機能（型エラー修正版）
"""

import pandas as pd
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any, Union
import logging
import os
from database.models import BodyStats

class ExcelBodyStatsImporter:
    """Excel体組成データ一括インポートクラス（型安全版）"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def import_from_excel(self, excel_path: str, overwrite: bool = True) -> Dict[str, int]:
        """
        Excelファイルから体組成データを一括インポート
        
        Args:
            excel_path: Excelファイルのパス
            overwrite: 既存データの上書き許可
            
        Returns:
            インポート結果の辞書
        """
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excelファイルが見つかりません: {excel_path}")
        
        try:
            self.logger.info(f"Excel読み込み開始: {excel_path}")
            
            # Excelファイル読み込み
            df = self._read_excel_file(excel_path)
            
            # データクリーニング・検証
            cleaned_data = self._clean_and_validate_data(df)
            
            # データベースにインポート
            import_result = self._import_to_database(cleaned_data, overwrite)
            
            self.logger.info(f"Excel一括インポート完了: {import_result}")
            return import_result
            
        except Exception as e:
            self.logger.error(f"Excel一括インポートエラー: {e}")
            raise
    
    def _read_excel_file(self, excel_path: str) -> pd.DataFrame:
        """Excelファイル読み込み（エンジン自動選択）"""
        try:
            # 複数のエンジンを試行（型安全な方法）
            engines = ['openpyxl', 'xlrd', None]  # None = デフォルトエンジン
            
            for engine in engines:
                try:
                    if engine is None:
                        df = pd.read_excel(excel_path)
                    else:
                        df = pd.read_excel(excel_path, engine=engine)
                    
                    self.logger.info(f"Excel読み込み成功 (engine={engine}): {len(df)}行, {len(df.columns)}列")
                    return df
                    
                except ImportError:
                    continue  # エンジンがインストールされていない場合
                except Exception as e:
                    if engine == engines[-1]:  # 最後のエンジンでも失敗
                        raise e
                    continue
            
            raise ValueError("すべてのExcelエンジンで読み込みに失敗しました")
            
        except Exception as e:
            raise ValueError(f"Excelファイル読み込みエラー: {e}")
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> List[Dict]:
        """データクリーニングと検証（型安全版）"""
        cleaned_records = []
        
        try:
            # ヘッダー行を探す（より安全な方法）
            header_row = self._find_header_row(df)
            
            if header_row is None:
                raise ValueError("ヘッダー行が見つかりません（'日付'を含む行が必要）")
            
            # ヘッダー行以降をデータとして使用
            data_df = df.iloc[header_row + 1:].copy()  # +1 でヘッダー行を除外
            data_df.columns = df.iloc[header_row].values  # ヘッダーを列名に設定
            
            # 列名マッピング（柔軟な対応）
            column_mapping = self._create_column_mapping(data_df.columns)
            
            # 各行をパース
            for idx, (index, row) in enumerate(data_df.iterrows()):
                try:
                    record = self._parse_row_safe(row, column_mapping)
                    if record:
                        cleaned_records.append(record)
                except Exception as e:
                    self.logger.warning(f"行 {idx + header_row + 2} のパースに失敗: {e}")
                    continue
            
            self.logger.info(f"データクリーニング完了: {len(cleaned_records)}件の有効なレコード")
            return cleaned_records
            
        except Exception as e:
            raise ValueError(f"データクリーニングエラー: {e}")
    
    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """ヘッダー行を探す（型安全版）"""
        for i in range(min(10, len(df))):  # 最初の10行まで探索
            row_values = df.iloc[i].values
            for cell in row_values:
                if pd.notna(cell) and '日付' in str(cell):
                    return i
        return None
    
    def _create_column_mapping(self, columns: pd.Index) -> Dict[str, Optional[str]]:
        """列名マッピング作成（型安全版）"""
        mapping: Dict[str, Optional[str]] = {
            'date': None,
            'weight': None,
            'body_fat_percentage': None,
            'muscle_mass': None
        }
        
        # 柔軟な列名マッチング
        for col in columns:
            if pd.isna(col):
                continue
            
            col_str = str(col).lower().strip()
            
            # 日付列
            if any(keyword in col_str for keyword in ['日付', 'date', '測定日']):
                mapping['date'] = str(col)
            
            # 体重列
            elif any(keyword in col_str for keyword in ['体重']) and 'kg' in col_str:
                mapping['weight'] = str(col)
            
            # 体脂肪率列
            elif any(keyword in col_str for keyword in ['脂肪率', '体脂肪', 'body_fat', 'bodyfat']):
                mapping['body_fat_percentage'] = str(col)
            
            # 筋肉量列
            elif any(keyword in col_str for keyword in ['筋肉量', 'muscle']) and 'kg' in col_str:
                mapping['muscle_mass'] = str(col)
        
        # デバッグ用ログ
        self.logger.debug(f"列マッピング結果: {mapping}")
        return mapping
    
    def _parse_row_safe(self, row: pd.Series, column_mapping: Dict[str, Optional[str]]) -> Optional[Dict]:
        """行データをパース（型安全版）"""
        try:
            # 日付パース（必須）
            date_col = column_mapping.get('date')
            if not date_col:
                return None
            
            # 型安全な列アクセス
            date_value = self._safe_get_column_value(row, date_col)
            if date_value is None or pd.isna(date_value):
                return None
            
            parsed_date = self._parse_date(date_value)
            if not parsed_date:
                return None
            
            # 数値データパース（型安全版）
            weight = self._parse_numeric_column(row, column_mapping.get('weight'))
            body_fat = self._parse_numeric_column(row, column_mapping.get('body_fat_percentage'))
            muscle_mass = self._parse_numeric_column(row, column_mapping.get('muscle_mass'))
            
            # 少なくとも体重は必須
            if weight is None:
                return None
            
            return {
                'date': parsed_date,
                'weight': weight,
                'body_fat_percentage': body_fat,
                'muscle_mass': muscle_mass
            }
            
        except Exception as e:
            self.logger.warning(f"行パースエラー: {e}")
            return None
    
    def _safe_get_column_value(self, row: pd.Series, column_name: Optional[str]) -> Any:
        """型安全な列値取得"""
        if column_name is None:
            return None
        
        try:
            # pandasの型チェックを回避するため、iloc を使用
            if column_name in row.index:
                return row[column_name]
            else:
                return None
        except (KeyError, IndexError):
            return None
    
    def _parse_numeric_column(self, row: pd.Series, column_name: Optional[str]) -> Optional[float]:
        """数値列をパース（型安全版）"""
        if column_name is None:
            return None
        
        value = self._safe_get_column_value(row, column_name)
        return self._parse_float(value)
    
    def _parse_date(self, date_value: Any) -> Optional[date]:
        """日付パース（改良版）"""
        try:
            if pd.isna(date_value):
                return None
            
            # 既にdatetimeオブジェクトの場合
            if isinstance(date_value, datetime):
                return date_value.date()
            elif isinstance(date_value, date):
                return date_value
            
            # 文字列の場合
            if isinstance(date_value, str):
                date_str = date_value.strip()
                if not date_str:
                    return None
                
                # 複数の日付フォーマットに対応
                formats = [
                    '%Y/%m/%d',
                    '%Y-%m-%d', 
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                    '%Y年%m月%d日',
                    '%Y.%m.%d'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
            
            # 数値（Excelのシリアル値）の場合
            if isinstance(date_value, (int, float)):
                try:
                    # Excelの日付シリアル値から変換
                    excel_date = datetime(1900, 1, 1) + pd.Timedelta(days=int(date_value) - 2)
                    return excel_date.date()
                except (ValueError, OverflowError):
                    pass
            
            return None
            
        except Exception as e:
            self.logger.debug(f"日付パースエラー: {date_value} -> {e}")
            return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """浮動小数点数パース（改良版）"""
        try:
            if pd.isna(value):
                return None
            
            # 既に数値の場合
            if isinstance(value, (int, float)):
                return float(value)
            
            # 文字列の場合、数値部分のみ抽出
            if isinstance(value, str):
                value_str = value.strip()
                if not value_str:
                    return None
                
                import re
                # 数値部分を抽出（小数点、負数対応）
                match = re.search(r'(-?\d+\.?\d*)', value_str.replace(',', ''))
                if match:
                    return float(match.group(1))
                return None
            
            # その他の型は文字列化してから変換を試す
            return float(str(value))
            
        except (ValueError, TypeError) as e:
            self.logger.debug(f"数値パースエラー: {value} -> {e}")
            return None
    
    def _import_to_database(self, records: List[Dict], overwrite: bool) -> Dict[str, int]:
        """データベースにインポート"""
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for record in records:
            try:
                # 既存データチェック
                existing = self.db_manager.get_body_stats_by_date(record['date'])
                
                if existing:
                    if overwrite:
                        # 既存データ更新
                        existing.weight = record.get('weight') or existing.weight
                        existing.body_fat_percentage = record.get('body_fat_percentage') or existing.body_fat_percentage
                        existing.muscle_mass = record.get('muscle_mass') or existing.muscle_mass
                        
                        if self.db_manager.update_body_stats(existing):
                            updated_count += 1
                        else:
                            error_count += 1
                    else:
                        skipped_count += 1
                else:
                    # 新規データ追加
                    body_stats = BodyStats(
                        id=None,
                        date=record['date'],
                        weight=record.get('weight'),
                        body_fat_percentage=record.get('body_fat_percentage'),
                        muscle_mass=record.get('muscle_mass')
                    )
                    
                    if self.db_manager.add_body_stats(body_stats):
                        imported_count += 1
                    else:
                        error_count += 1
                        
            except Exception as e:
                self.logger.error(f"レコードインポートエラー: {e}")
                error_count += 1
                continue
        
        return {
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_processed': len(records)
        }
    
    def preview_import_data(self, excel_path: str) -> Dict:
        """インポート前プレビュー"""
        try:
            df = self._read_excel_file(excel_path)
            cleaned_data = self._clean_and_validate_data(df)
            
            if not cleaned_data:
                return {'error': 'インポート可能なデータが見つかりません'}
            
            # 統計情報計算
            stats = self._calculate_preview_stats(cleaned_data)
            
            return {
                'success': True,
                'total_records': len(cleaned_data),
                'date_range': {
                    'start': min(r['date'] for r in cleaned_data),
                    'end': max(r['date'] for r in cleaned_data)
                },
                'data_types': {
                    'weight': sum(1 for r in cleaned_data if r.get('weight')),
                    'body_fat': sum(1 for r in cleaned_data if r.get('body_fat_percentage')),
                    'muscle_mass': sum(1 for r in cleaned_data if r.get('muscle_mass'))
                },
                'sample_data': cleaned_data[:5],  # 最初の5件
                'stats': stats
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_preview_stats(self, records: List[Dict]) -> Dict:
        """プレビュー統計計算"""
        stats = {}
        
        # 体重統計
        weights = [r['weight'] for r in records if r.get('weight')]
        if weights:
            stats['weight'] = {
                'min': min(weights),
                'max': max(weights),
                'avg': sum(weights) / len(weights),
                'count': len(weights)
            }
        
        # 体脂肪率統計
        body_fats = [r['body_fat_percentage'] for r in records if r.get('body_fat_percentage')]
        if body_fats:
            stats['body_fat'] = {
                'min': min(body_fats),
                'max': max(body_fats),
                'avg': sum(body_fats) / len(body_fats),
                'count': len(body_fats)
            }
        
        # 筋肉量統計
        muscles = [r['muscle_mass'] for r in records if r.get('muscle_mass')]
        if muscles:
            stats['muscle_mass'] = {
                'min': min(muscles),
                'max': max(muscles),
                'avg': sum(muscles) / len(muscles),
                'count': len(muscles)
            }
        
        return stats
    
    def validate_excel_format(self, excel_path: str) -> Dict[str, Any]:
        """Excelファイル形式検証"""
        try:
            df = self._read_excel_file(excel_path)
            
            # ヘッダー行チェック
            header_row = self._find_header_row(df)
            if header_row is None:
                return {
                    'valid': False,
                    'error': '日付列が見つかりません。「日付」を含むヘッダーが必要です。'
                }
            
            # 列マッピングチェック
            data_df = df.iloc[header_row + 1:].copy()
            data_df.columns = df.iloc[header_row].values
            column_mapping = self._create_column_mapping(data_df.columns)
            
            missing_columns = []
            if not column_mapping.get('date'):
                missing_columns.append('日付')
            if not column_mapping.get('weight'):
                missing_columns.append('体重')
            
            if missing_columns:
                return {
                    'valid': False,
                    'error': f'必須列が見つかりません: {", ".join(missing_columns)}'
                }
            
            # データ行チェック
            data_rows = len(data_df)
            if data_rows == 0:
                return {
                    'valid': False,
                    'error': 'データ行が見つかりません。'
                }
            
            return {
                'valid': True,
                'header_row': header_row,
                'data_rows': data_rows,
                'columns': column_mapping,
                'message': f'有効なExcelファイルです。{data_rows}行のデータが検出されました。'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'ファイル検証エラー: {str(e)}'
            }