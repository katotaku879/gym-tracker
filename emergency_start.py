#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急起動スクリプト（最小構成）
emergency_start.py として保存
"""

import sys
import os

print("🚀 GymTracker 緊急起動")
print("=" * 30)

try:
    # 基本チェック
    from PySide6.QtWidgets import QApplication
    print("✅ PySide6 OK")
    
    # パス設定
    sys.path.insert(0, os.getcwd())
    
    # アプリ起動
    from ui.main_window import MainWindow
    print("✅ UIモジュール OK")
    
    app = QApplication(sys.argv)
    app.setApplicationName("GymTracker")
    
    window = MainWindow()
    window.show()
    
    print("✅ 起動成功！")
    print("🎯 新しい「体組成目標」タブを確認してください")
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    input("Enterキーで終了...")