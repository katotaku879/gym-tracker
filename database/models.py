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