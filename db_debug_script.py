# db_debug_script.py
# データベースの詳細診断

import sqlite3
import os

def check_database_files():
    """データベースファイルを全て確認"""
    print("🔍 データベースファイルを検索中...")
    
    # 現在のディレクトリでdbファイルを探す
    db_files = []
    for file in os.listdir('.'):
        if file.endswith('.db'):
            db_files.append(file)
    
    print(f"📁 見つかったデータベースファイル: {db_files}")
    return db_files

def analyze_database(db_file):
    """データベースファイルの詳細分析"""
    print(f"\n📊 {db_file} の分析:")
    print("-" * 50)
    
    try:
        conn = sqlite3.connect(db_file)
        
        # テーブル一覧
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 テーブル一覧: {tables}")
        
        # goalsテーブルの詳細
        if 'goals' in tables:
            print("\n🎯 goalsテーブルの構造:")
            cursor = conn.execute("PRAGMA table_info(goals)")
            columns = []
            for row in cursor.fetchall():
                columns.append(f"{row[1]} ({row[2]})")
            print(f"   カラム: {columns}")
            
            # データ件数
            cursor = conn.execute("SELECT COUNT(*) FROM goals")
            count = cursor.fetchone()[0]
            print(f"   データ件数: {count}件")
            
            # サンプルデータ（あれば）
            if count > 0:
                cursor = conn.execute("SELECT * FROM goals LIMIT 3")
                sample_data = cursor.fetchall()
                print(f"   サンプルデータ: {sample_data}")
        else:
            print("❌ goalsテーブルが存在しません")
        
        # exercisesテーブルの確認
        if 'exercises' in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM exercises")
            exercise_count = cursor.fetchone()[0]
            print(f"📝 exercisesテーブル: {exercise_count}件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析エラー: {e}")

def check_database_creation():
    """データベース作成プロセスをシミュレート"""
    print("\n🧪 データベース作成テスト:")
    print("-" * 50)
    
    # テスト用データベース作成
    test_db = "test_goals.db"
    
    try:
        # 既存のテストファイルを削除
        if os.path.exists(test_db):
            os.remove(test_db)
        
        conn = sqlite3.connect(test_db)
        
        # アプリと同じ方法でテーブル作成
        print("🔨 古い形式のgoalsテーブルを作成...")
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
        
        # テーブル構造確認
        cursor = conn.execute("PRAGMA table_info(goals)")
        old_columns = [row[1] for row in cursor.fetchall()]
        print(f"   古い形式のカラム: {old_columns}")
        
        # v2形式に更新してみる
        print("\n🔄 v2形式への更新テスト...")
        
        # バックアップ作成
        conn.execute("CREATE TABLE goals_backup AS SELECT * FROM goals")
        
        # テーブル削除・再作成
        conn.execute("DROP TABLE goals")
        
        conn.execute("""
            CREATE TABLE goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id INTEGER NOT NULL,
                target_weight REAL NOT NULL,
                target_reps INTEGER NOT NULL DEFAULT 8,
                target_sets INTEGER NOT NULL DEFAULT 3,
                current_achieved_sets INTEGER DEFAULT 0,
                current_max_weight REAL DEFAULT 0.0,
                target_month TEXT NOT NULL,
                achieved BOOLEAN DEFAULT FALSE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exercise_id) REFERENCES exercises (id),
                UNIQUE(exercise_id, target_month)
            )
        """)
        
        # 新しい構造確認
        cursor = conn.execute("PRAGMA table_info(goals)")
        new_columns = [row[1] for row in cursor.fetchall()]
        print(f"   v2形式のカラム: {new_columns}")
        
        conn.close()
        
        # テストファイルクリーンアップ
        os.remove(test_db)
        
        print("✅ テーブル更新テスト成功")
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        if os.path.exists(test_db):
            os.remove(test_db)

def main():
    print("🔧 GymTracker データベース診断ツール")
    print("=" * 60)
    
    # 1. データベースファイル確認
    db_files = check_database_files()
    
    # 2. 各ファイルの詳細分析
    for db_file in db_files:
        analyze_database(db_file)
    
    # 3. データベース作成プロセステスト
    check_database_creation()
    
    print("\n🎯 診断結果まとめ:")
    print("=" * 60)
    if 'gym_tracker.db' in db_files:
        print("✅ メインデータベースファイル存在")
        print("📝 上記の分析結果を確認してください")
        print("\n💡 解決方法:")
        print("1. アプリを完全に終了")
        print("2. gym_tracker.db のgoalsテーブルがv2形式か確認")
        print("3. 必要に応じてテーブル再作成")
    else:
        print("❌ gym_tracker.db が見つかりません")
        print("💡 アプリを一度起動してデータベースを作成してください")

if __name__ == "__main__":
    main()