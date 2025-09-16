# utils/validation.py
from typing import Optional, Tuple
from .constants import WEIGHT_MIN, WEIGHT_MAX, REPS_MIN, REPS_MAX

class ValidationError(Exception):
    """入力値検証エラー"""
    pass

def validate_weight(weight: float) -> Tuple[bool, Optional[str]]:
    """重量検証"""
    try:
        if not isinstance(weight, (int, float)):
            return False, "重量は数値で入力してください"
        
        if weight < WEIGHT_MIN:
            return False, f"重量は{WEIGHT_MIN}kg以上で入力してください"
        
        if weight > WEIGHT_MAX:
            return False, f"重量は{WEIGHT_MAX}kg以下で入力してください"
        
        # 2.5kg刻みチェックを削除
        # より細かい刻み（0.5kg刻み）まで許可
        if round(weight * 2) != weight * 2:
            return False, "重量は0.5kg刻みで入力してください"
        
        return True, None
    except Exception as e:
        return False, f"重量の検証でエラーが発生しました: {e}"

def validate_reps(reps: int) -> Tuple[bool, Optional[str]]:
    """回数検証"""
    try:
        if not isinstance(reps, int):
            return False, "回数は整数で入力してください"
        
        if reps < REPS_MIN:
            return False, f"回数は{REPS_MIN}回以上で入力してください"
        
        if reps > REPS_MAX:
            return False, f"回数は{REPS_MAX}回以下で入力してください"
        
        return True, None
    except Exception as e:
        return False, f"回数の検証でエラーが発生しました: {e}"

def validate_set_data(weight: float, reps: int) -> Tuple[bool, Optional[str]]:
    """セットデータ全体検証"""
    # 重量検証
    weight_valid, weight_error = validate_weight(weight)
    if not weight_valid:
        return False, weight_error
    
    # 回数検証
    reps_valid, reps_error = validate_reps(reps)
    if not reps_valid:
        return False, reps_error
    
    return True, None