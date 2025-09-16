# ui/body_stats_dialog.py - 型エラー修正版
from datetime import date, datetime
from typing import Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                               QDateEdit, QDoubleSpinBox, QDialogButtonBox)
from PySide6.QtCore import QDate

from database.models import BodyStats

class BodyStatsDialog(QDialog):
    """体組成データ入力ダイアログ"""
    
    def __init__(self, db_manager, body_stats: Optional[BodyStats] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.body_stats = body_stats
        self.init_ui()
        
        if body_stats:
            self.setWindowTitle("体組成データ編集")
            self.load_data()
        else:
            self.setWindowTitle("体組成データ追加")
    
    def init_ui(self):
        """UI初期化"""
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # フォームレイアウト
        form_layout = QFormLayout()
        
        # 日付
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("日付:", self.date_edit)
        
        # 体重
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setMinimum(20.0)
        self.weight_spin.setMaximum(300.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setDecimals(1)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setSpecialValueText("未入力")
        form_layout.addRow("体重:", self.weight_spin)
        
        # 体脂肪率
        self.body_fat_spin = QDoubleSpinBox()
        self.body_fat_spin.setMinimum(0.0)
        self.body_fat_spin.setMaximum(50.0)
        self.body_fat_spin.setSingleStep(0.1)
        self.body_fat_spin.setDecimals(1)
        self.body_fat_spin.setSuffix(" %")
        self.body_fat_spin.setSpecialValueText("未入力")
        form_layout.addRow("体脂肪率:", self.body_fat_spin)
        
        # 筋肉量
        self.muscle_mass_spin = QDoubleSpinBox()
        self.muscle_mass_spin.setMinimum(0.0)
        self.muscle_mass_spin.setMaximum(100.0)
        self.muscle_mass_spin.setSingleStep(0.1)
        self.muscle_mass_spin.setDecimals(1)
        self.muscle_mass_spin.setSuffix(" kg")
        self.muscle_mass_spin.setSpecialValueText("未入力")
        form_layout.addRow("筋肉量:", self.muscle_mass_spin)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_data(self):
        """データ読み込み（型安全版）"""
        if not self.body_stats:
            return
        
        # 日付設定（型安全な変換）
        try:
            if isinstance(self.body_stats.date, str):
                # 文字列から日付オブジェクトに変換
                date_obj = datetime.strptime(self.body_stats.date, '%Y-%m-%d').date()
            elif isinstance(self.body_stats.date, date):
                # 既にdateオブジェクトの場合
                date_obj = self.body_stats.date
            else:
                # その他の場合は今日の日付を使用
                date_obj = date.today()
            
            # dateオブジェクトからQDateに変換（型安全）
            qdate = QDate(date_obj.year, date_obj.month, date_obj.day)
            self.date_edit.setDate(qdate)
            
        except (ValueError, AttributeError) as e:
            # エラーの場合は今日の日付を設定
            self.date_edit.setDate(QDate.currentDate())
            print(f"Date conversion error: {e}")
        
        # 各値設定（None チェック付き）
        if self.body_stats.weight is not None:
            self.weight_spin.setValue(float(self.body_stats.weight))
        else:
            self.weight_spin.setValue(self.weight_spin.minimum())  # 最小値に設定
        
        if self.body_stats.body_fat_percentage is not None:
            self.body_fat_spin.setValue(float(self.body_stats.body_fat_percentage))
        else:
            self.body_fat_spin.setValue(self.body_fat_spin.minimum())
        
        if self.body_stats.muscle_mass is not None:
            self.muscle_mass_spin.setValue(float(self.body_stats.muscle_mass))
        else:
            self.muscle_mass_spin.setValue(self.muscle_mass_spin.minimum())
    
    def get_body_stats(self) -> BodyStats:
        """体組成データ取得（型安全版）"""
        # QDateからPythonのdateオブジェクトに安全に変換
        qdate = self.date_edit.date()
        try:
            # toPython()メソッドを使用して安全に変換
            date_obj = qdate.toPython()
            # 型が正しいことを確認
            if not isinstance(date_obj, date):
                raise ValueError("Date conversion failed")
        except (AttributeError, ValueError):
            # フォールバック: 手動で変換
            date_obj = date(qdate.year(), qdate.month(), qdate.day())
        
        # 値が最小値の場合はNoneとして扱う
        weight_val = None
        if self.weight_spin.value() > self.weight_spin.minimum():
            weight_val = self.weight_spin.value()
        
        body_fat_val = None
        if self.body_fat_spin.value() > self.body_fat_spin.minimum():
            body_fat_val = self.body_fat_spin.value()
        
        muscle_mass_val = None
        if self.muscle_mass_spin.value() > self.muscle_mass_spin.minimum():
            muscle_mass_val = self.muscle_mass_spin.value()
        
        return BodyStats(
            id=self.body_stats.id if self.body_stats else None,
            date=date_obj,
            weight=weight_val,
            body_fat_percentage=body_fat_val,
            muscle_mass=muscle_mass_val
        )