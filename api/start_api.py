#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Startup Script for Disability Certificate AI Accuracy Evaluator API
身心障礙手冊AI測試結果準確度評分系統 - API啟動腳本
"""

import uvicorn
import sys
import os

def main():
    """主程式"""
    print("=" * 60)
    print("身心障礙手冊AI測試結果準確度評分系統")
    print("Disability Certificate AI Accuracy Evaluator API")
    print("=" * 60)
    
    # 檢查必要檔案
    script_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "app.py",
        "evaluator_core.py",
        "evaluator_service.py",
        "excel_generator.py",
        "models.py",
        "exceptions.py"
    ]

    missing_files = [f for f in required_files if not os.path.exists(os.path.join(script_dir, f))]
    if missing_files:
        print(f"❌ 缺少必要檔案: {missing_files}")
        sys.exit(1)
    
    print("✅ 所有必要檔案都存在")
    
    # 設定參數
    host = "0.0.0.0"
    port = 8000
    reload = True
    
    # 從命令列參數取得設定
    if len(sys.argv) > 1:
        if sys.argv[1] == "--prod":
            reload = False
            print("🚀 生產模式啟動")
        elif sys.argv[1] == "--help":
            print_help()
            return
    else:
        print("🔧 開發模式啟動 (自動重載)")
    
    print(f"📡 服務將在 http://{host}:{port} 啟動")
    print(f"📚 API文檔: http://localhost:{port}/docs")
    print(f"📖 ReDoc: http://localhost:{port}/redoc")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "api.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 API服務已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {str(e)}")
        sys.exit(1)

def print_help():
    """顯示幫助訊息"""
    print("""
使用方式:
    python start_api.py [選項]

選項:
    --prod      生產模式啟動 (關閉自動重載)
    --help      顯示此幫助訊息

範例:
    python start_api.py              # 開發模式
    python start_api.py --prod       # 生產模式
    
API端點:
    GET  /                          # API資訊
    GET  /health                    # 健康檢查
    POST /evaluate                  # 檔案評估
    GET  /docs                      # Swagger文檔
    GET  /redoc                     # ReDoc文檔

測試:
    python test_api.py              # 執行API測試
    """)

if __name__ == "__main__":
    main()
