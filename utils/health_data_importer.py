# utils/health_data_importer.py - 完全版（エラーハンドリング強化）
"""
Appleヘルスアプリからの体重データ移行スクリプト
"""

import xml.etree.ElementTree as ET
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
import logging
import os

class HealthDataImporter:
    """Appleヘルスデータ移行クラス"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def import_from_export_xml(self, export_xml_path: str) -> Dict[str, int]:
        """
        AppleヘルスのXMLエクスポートファイルから体重データをインポート
        
        Args:
            export_xml_path: export.xmlファイルのパス
            
        Returns:
            インポート結果の辞書
        """
        if not os.path.exists(export_xml_path):
            raise FileNotFoundError(f"XMLファイルが見つかりません: {export_xml_path}")
        
        # ファイルサイズチェック
        file_size = os.path.getsize(export_xml_path) / (1024 * 1024)  # MB
        if file_size > 500:  # 500MB以上の場合警告
            self.logger.warning(f"Large XML file detected: {file_size:.1f}MB")
        
        try:
            # XMLファイルを読み込み
            self.logger.info(f"XMLファイルを読み込み中: {export_xml_path}")
            tree = ET.parse(export_xml_path)
            root = tree.getroot()
            
            # データ抽出
            weight_records = self._extract_weight_records(root)
            body_fat_records = self._extract_body_fat_records(root)
            
            # データベースにインポート
            imported_weight = self._import_weight_data(weight_records)
            imported_body_fat = self._import_body_fat_data(body_fat_records)
            
            result = {
                'weight_records': imported_weight,
                'body_fat_records': imported_body_fat,
                'total': imported_weight + imported_body_fat
            }
            
            self.logger.info(f"データ移行完了: {result}")
            return result
            
        except ET.ParseError as e:
            self.logger.error(f"XMLファイルの解析に失敗: {e}")
            raise ValueError(f"XMLファイルの形式が不正です: {e}")
        except Exception as e:
            self.logger.error(f"データ移行中にエラー: {e}")
            raise
    
    def _extract_weight_records(self, root) -> List[Dict]:
        """体重レコードを抽出"""
        weight_records = []
        
        # HKQuantityTypeIdentifierBodyMass が体重データ
        for record in root.findall(".//Record[@type='HKQuantityTypeIdentifierBodyMass']"):
            try:
                # 日時情報
                start_date = record.get('startDate')
                value = record.get('value')
                unit = record.get('unit', 'kg')
                
                if start_date and value:
                    # ISO形式の日時をパース
                    dt = self._parse_apple_datetime(start_date)
                    
                    if dt:
                        weight_records.append({
                            'date': dt.date(),
                            'weight': float(value),
                            'unit': unit
                        })
            except (ValueError, TypeError) as e:
                self.logger.warning(f"体重レコードのパースに失敗: {e}")
                continue
        
        # 日付でソート（古い順）
        weight_records.sort(key=lambda x: x['date'])
        self.logger.info(f"体重レコード抽出: {len(weight_records)}件")
        
        return weight_records
    
    def _extract_body_fat_records(self, root) -> List[Dict]:
        """体脂肪率レコードを抽出"""
        body_fat_records = []
        
        # HKQuantityTypeIdentifierBodyFatPercentage が体脂肪率データ
        for record in root.findall(".//Record[@type='HKQuantityTypeIdentifierBodyFatPercentage']"):
            try:
                start_date = record.get('startDate')
                value = record.get('value')
                
                if start_date and value:
                    dt = self._parse_apple_datetime(start_date)
                    
                    if dt:
                        # パーセンテージ値（0.15 → 15%）
                        percentage = float(value) * 100
                        
                        body_fat_records.append({
                            'date': dt.date(),
                            'body_fat_percentage': percentage
                        })
            except (ValueError, TypeError) as e:
                self.logger.warning(f"体脂肪率レコードのパースに失敗: {e}")
                continue
        
        body_fat_records.sort(key=lambda x: x['date'])
        self.logger.info(f"体脂肪率レコード抽出: {len(body_fat_records)}件")
        
        return body_fat_records
    
    def _parse_apple_datetime(self, date_string: str) -> Optional[datetime]:
        """Appleヘルスの日時文字列をパース"""
        try:
            # Apple Healthの日時形式パターン
            patterns = [
                '%Y-%m-%d %H:%M:%S %z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            # タイムゾーン記号を処理
            cleaned_date = date_string.replace('Z', '+0000')
            
            for pattern in patterns:
                try:
                    return datetime.strptime(cleaned_date, pattern)
                except ValueError:
                    continue
            
            # フォールバック: ISOフォーマット
            return datetime.fromisoformat(cleaned_date.replace('Z', '+00:00'))
            
        except Exception as e:
            self.logger.warning(f"Date parsing failed for {date_string}: {e}")
            return None
    
    def _import_weight_data(self, weight_records: List[Dict]) -> int:
        """体重データをデータベースにインポート"""
        imported_count = 0
        
        for record in weight_records:
            try:
                # 既存データチェック
                existing = self.db_manager.get_body_stats_by_date(record['date'])
                
                if existing:
                    # 既存データがある場合は体重のみ更新
                    existing.weight = record['weight']
                    if self.db_manager.update_body_stats(existing):
                        imported_count += 1
                        self.logger.debug(f"体重更新: {record['date']} - {record['weight']}kg")
                else:
                    # 新規データ作成
                    from database.models import BodyStats
                    
                    body_stats = BodyStats(
                        id=None,
                        date=record['date'],
                        weight=record['weight'],
                        body_fat_percentage=None,
                        muscle_mass=None
                    )
                    
                    if self.db_manager.add_body_stats(body_stats):
                        imported_count += 1
                        self.logger.debug(f"体重追加: {record['date']} - {record['weight']}kg")
                        
            except Exception as e:
                self.logger.error(f"体重データインポートエラー: {e}")
                continue
        
        return imported_count
    
    def _import_body_fat_data(self, body_fat_records: List[Dict]) -> int:
        """体脂肪率データをインポート"""
        imported_count = 0
        
        for record in body_fat_records:
            try:
                existing = self.db_manager.get_body_stats_by_date(record['date'])
                
                if existing:
                    # 体脂肪率のみ更新
                    existing.body_fat_percentage = record['body_fat_percentage']
                    if self.db_manager.update_body_stats(existing):
                        imported_count += 1
                else:
                    # 新規データ作成
                    from database.models import BodyStats
                    
                    body_stats = BodyStats(
                        id=None,
                        date=record['date'],
                        weight=None,
                        body_fat_percentage=record['body_fat_percentage'],
                        muscle_mass=None
                    )
                    
                    if self.db_manager.add_body_stats(body_stats):
                        imported_count += 1
                        
            except Exception as e:
                self.logger.error(f"体脂肪率データインポートエラー: {e}")
                continue
        
        return imported_count
    
    def preview_import_data(self, export_xml_path: str) -> Dict:
        """インポート前のプレビュー"""
        try:
            tree = ET.parse(export_xml_path)
            root = tree.getroot()
            
            weight_records = self._extract_weight_records(root)
            body_fat_records = self._extract_body_fat_records(root)
            
            # 統計情報
            weight_stats = self._calculate_preview_stats(weight_records, 'weight')
            body_fat_stats = self._calculate_preview_stats(body_fat_records, 'body_fat_percentage')
            
            return {
                'weight': {
                    'count': len(weight_records),
                    'date_range': weight_stats,
                    'sample': weight_records[:5]  # 最初の5件
                },
                'body_fat': {
                    'count': len(body_fat_records),
                    'date_range': body_fat_stats,
                    'sample': body_fat_records[:5]
                }
            }
            
        except Exception as e:
            self.logger.error(f"プレビュー生成エラー: {e}")
            raise
    
    def _calculate_preview_stats(self, records: List[Dict], value_key: str) -> Dict:
        """プレビュー用統計計算"""
        if not records:
            return {'start_date': None, 'end_date': None, 'min_value': None, 'max_value': None}
        
        values = [record[value_key] for record in records if record.get(value_key)]
        
        return {
            'start_date': records[0]['date'],
            'end_date': records[-1]['date'],
            'min_value': min(values) if values else None,
            'max_value': max(values) if values else None,
            'average': sum(values) / len(values) if values else None
        }