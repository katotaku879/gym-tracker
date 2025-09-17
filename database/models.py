# database/models.py
"""データベースモデル定義"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Exercise:
    """種目モデル"""
    id: Optional[int]
    name: str
    variation: str
    category: str
    
    def display_name(self) -> str:
        """表示用名称"""
        return f"{self.name}（{self.variation}）"

@dataclass
class Workout:
    """ワークアウトモデル"""
    id: Optional[int]
    date: date
    notes: Optional[str] = None

@dataclass
class Set:
    """セットモデル"""
    id: Optional[int]
    workout_id: int
    exercise_id: int
    set_number: int
    weight: float
    reps: int
    one_rm: Optional[float] = None

@dataclass
class Goal:
    """目標モデル"""
    id: Optional[int]
    exercise_id: int
    target_weight: float
    current_weight: float
    target_month: str  # YYYY-MM
    achieved: bool = False

@dataclass
class BodyStats:
    """体組成データモデル"""
    id: Optional[int]
    date: date
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None

@dataclass
class BodyCompositionGoal:
    """体組成目標モデル"""
    id: Optional[int]
    goal_name: str                      # 目標名 (例: "夏までの減量目標")
    target_weight: Optional[float]      # 目標体重 (kg)
    target_muscle_mass: Optional[float] # 目標筋肉量 (kg)
    target_body_fat: Optional[float]    # 目標体脂肪率 (%)
    target_bmi: Optional[float]         # 目標BMI
    target_date: date                   # 目標達成日
    current_weight: Optional[float] = None      # 現在体重
    current_muscle_mass: Optional[float] = None # 現在筋肉量
    current_body_fat: Optional[float] = None    # 現在体脂肪率
    current_bmi: Optional[float] = None         # 現在BMI
    achieved: bool = False              # 達成フラグ
    notes: Optional[str] = None         # メモ
    created_at: Optional[str] = None    # 作成日
    updated_at: Optional[str] = None    # 更新日
    
    def calculate_bmi(self, weight: float, height_cm: float) -> float:
        """BMI計算"""
        if weight <= 0 or height_cm <= 0:
            return 0.0
        height_m = height_cm / 100
        return round(weight / (height_m ** 2), 1)
    
    def weight_progress_percentage(self, initial_weight: Optional[float] = None) -> int:
        """体重目標の進捗率計算"""
        if not self.target_weight or not self.current_weight:
            return 0
        
        # 初期体重が提供されない場合は、現在重量を基準とする
        if initial_weight is None:
            initial_weight = self.current_weight
        
        # 目標が現在より上か下かで計算方法を変える
        if self.target_weight > initial_weight:
            # 増量目標の場合
            total_change = self.target_weight - initial_weight
            current_change = self.current_weight - initial_weight
        else:
            # 減量目標の場合
            total_change = initial_weight - self.target_weight
            current_change = initial_weight - self.current_weight
        
        if total_change <= 0:
            return 100
        
        progress = int((current_change / total_change) * 100)
        return max(0, min(progress, 100))
    
    def muscle_progress_percentage(self, initial_muscle: Optional[float] = None) -> int:
        """筋肉量目標の進捗率計算"""
        if not self.target_muscle_mass or not self.current_muscle_mass:
            return 0
        
        # 初期筋肉量が提供されない場合は、現在重量の90%を仮定
        if initial_muscle is None:
            initial_muscle = self.current_muscle_mass * 0.9
        
        # 筋肉量は通常増加目標
        if self.current_muscle_mass >= self.target_muscle_mass:
            return 100
        
        total_change = self.target_muscle_mass - initial_muscle
        current_change = self.current_muscle_mass - initial_muscle
        
        if total_change <= 0:
            return 100
        
        progress = int((current_change / total_change) * 100)
        return max(0, min(progress, 100))
    
    def body_fat_progress_percentage(self, initial_body_fat: Optional[float] = None) -> int:
        """体脂肪率目標の進捗率計算"""
        if not self.target_body_fat or not self.current_body_fat:
            return 0
        
        # 初期体脂肪率が提供されない場合は、現在値の110%を仮定
        if initial_body_fat is None:
            initial_body_fat = self.current_body_fat * 1.1
        
        # 体脂肪率は通常減少目標
        if self.current_body_fat <= self.target_body_fat:
            return 100
        
        total_change = initial_body_fat - self.target_body_fat
        current_change = initial_body_fat - self.current_body_fat
        
        if total_change <= 0:
            return 100
        
        progress = int((current_change / total_change) * 100)
        return max(0, min(progress, 100))
    
    def is_overdue(self) -> bool:
        """期限切れ判定"""
        from datetime import date as dt
        return self.target_date < dt.today() and not self.achieved
    
    def days_remaining(self) -> int:
        """残り日数計算"""
        from datetime import date as dt
        delta = (self.target_date - dt.today()).days
        return max(0, delta)
    
    def overall_progress_percentage(self, 
                                    initial_weight: Optional[float] = None,
                                    initial_muscle: Optional[float] = None,
                                    initial_body_fat: Optional[float] = None) -> int:
        """総合進捗率（設定された目標の平均）"""
        progress_list = []
        
        if self.target_weight:
            progress_list.append(self.weight_progress_percentage(initial_weight))
        if self.target_muscle_mass:
            progress_list.append(self.muscle_progress_percentage(initial_muscle))
        if self.target_body_fat:
            progress_list.append(self.body_fat_progress_percentage(initial_body_fat))
        
        if not progress_list:
            return 0
        
        return int(sum(progress_list) / len(progress_list))
    
    def get_status_text(self) -> str:
        """ステータステキスト取得"""
        if self.achieved:
            return "✅ 達成済み"
        elif self.is_overdue():
            return "⏰ 期限切れ"
        else:
            days = self.days_remaining()
            if days == 0:
                return "🔥 今日が期限"
            elif days <= 7:
                return f"⚡ あと{days}日"
            else:
                return f"📅 あと{days}日"
    
    def get_target_summary(self) -> str:
        """目標サマリーテキスト"""
        targets = []
        if self.target_weight:
            targets.append(f"体重{self.target_weight}kg")
        if self.target_muscle_mass:
            targets.append(f"筋肉{self.target_muscle_mass}kg")
        if self.target_body_fat:
            targets.append(f"体脂肪{self.target_body_fat}%")
        if self.target_bmi:
            targets.append(f"BMI{self.target_bmi}")
        
        return " / ".join(targets) if targets else "目標未設定"