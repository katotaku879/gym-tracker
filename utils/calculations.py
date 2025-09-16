# utils/calculations.py
"""計算ユーティリティ"""

def calculate_one_rm(weight: float, reps: int) -> float:
    """
    1RM計算（Epley式）
    Args:
        weight: 実際に挙げた重量（kg）
        reps: 反復回数
    Returns:
        推定1RM（kg）
    """
    if reps == 1:
        return weight
    return weight * (1 + reps / 30)

def calculate_growth_rate(current: float, previous: float) -> float:
    """
    成長率計算
    Args:
        current: 現在の値
        previous: 前回の値
    Returns:
        成長率（%）
    """
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def calculate_total_volume(sets_data: list) -> float:
    """
    総ボリューム計算（重量 × 回数の合計）
    Args:
        sets_data: [{'weight': float, 'reps': int}, ...]
    Returns:
        総ボリューム
    """
    return sum(set_data['weight'] * set_data['reps'] for set_data in sets_data)

def calculate_average_weight(sets_data: list) -> float:
    """
    平均重量計算
    Args:
        sets_data: [{'weight': float, 'reps': int}, ...]
    Returns:
        平均重量
    """
    if not sets_data:
        return 0
    return sum(set_data['weight'] for set_data in sets_data) / len(sets_data)

def calculate_max_one_rm(sets_data: list) -> float:
    """
    セット群から最大1RMを計算
    Args:
        sets_data: [{'weight': float, 'reps': int}, ...]
    Returns:
        最大1RM
    """
    if not sets_data:
        return 0
    
    one_rms = [calculate_one_rm(set_data['weight'], set_data['reps']) 
               for set_data in sets_data]
    return max(one_rms)