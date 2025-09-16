# utils/constants.py
"""定数定義"""

# データベース設定
DB_FILE = "gym_tracker.db"

# 入力値制限
WEIGHT_MIN = 0.0
WEIGHT_MAX = 500.0
WEIGHT_STEP = 0.5  # 0.5kg刻みに変更

REPS_MIN = 1
REPS_MAX = 50

# ウィンドウサイズ
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1024
WINDOW_DEFAULT_HEIGHT = 768

# カテゴリー定義
EXERCISE_CATEGORIES = ["胸", "背中", "脚", "肩", "腕"]

# グラフ設定
GRAPH_COLORS = {
    "primary": "#2E86C1",
    "secondary": "#28B463", 
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "info": "#8E44AD"
}

# アプリケーション情報
APP_NAME = "GymTracker"
APP_VERSION = "1.0"
APP_AUTHOR = "GymTracker Team"