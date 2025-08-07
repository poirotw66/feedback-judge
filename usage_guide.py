#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身心障礙手冊AI測試結果準確度評分系統 - 使用說明書
Disability Certificate AI Test Result Accuracy Evaluation System - User Manual
"""

import os
import pandas as pd


def print_usage_guide():
    """列印使用說明"""
    guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     身心障礙手冊AI測試結果準確度評分系統                      ║
║                   Disability Certificate AI Accuracy Evaluation              ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 系統功能概述
────────────────────────────────────────────────────────────────────────────────
✅ 自動讀取Excel檔案中的身心障礙手冊測試資料
✅ 智能識別正面（人工標註）和反面（AI預測）資料欄位
✅ 計算各項目的準確度、匹配率和相似度
✅ 生成詳細的評估報告和錯誤分析
✅ 支援多種資料格式和欄位配置

📁 檔案結構說明
────────────────────────────────────────────────────────────────────────────────
├── accuracy_evaluator.py      # 核心評估引擎
├── main.py                   # 基本範例程式
├── excel_processor.py        # Excel檔案處理器
├── smart_processor.py        # 智能處理器（推薦使用）
├── detailed_evaluator.py     # 按編號詳細分析器（新功能）
├── usage_guide.py           # 本說明檔案
└── README.md                # 專案說明

📊 支援的資料欄位
────────────────────────────────────────────────────────────────────────────────
• 障礙等級 (輕度/中度/重度/極重度)
• 障礙類別 (第1類/第2類/其他類等)
• ICD診斷 (醫學診斷代碼)
• 證明/手冊類型

🚀 快速開始
────────────────────────────────────────────────────────────────────────────────
1. 確保您的Excel檔案包含正面（標準答案）和反面（AI預測）的資料
2. 選擇執行方式:
   
   ⭐ 整體準確度分析:
   python smart_processor.py
   
   ⭐ 按編號詳細分析（每個標號的欄位準確度）:
   python detailed_evaluator.py

3. 查看生成的結果檔案:
   - 智能評估結果_[檔案名].xlsx (整體分析結果)
   - 按編號詳細準確度分析.xlsx (每筆記錄詳細分析)
   - 終端顯示的摘要報告

💡 使用技巧
────────────────────────────────────────────────────────────────────────────────
• 程式會自動偵測Excel檔案的標題行位置
• 支援複雜的欄位名稱和多級標題
• 可自動處理欄位名稱中的空格和特殊字符
• 提供相似度分析，不只是完全匹配

📈 評估指標說明
────────────────────────────────────────────────────────────────────────────────
• 準確度: 基於字串相似度的平均分數 (0-100%)
• 完全匹配: 完全相同的項目數量
• 匹配率: 完全匹配項目的百分比
• 相似度: 使用序列匹配算法計算的文字相似程度

⚙️ 自訂設定
────────────────────────────────────────────────────────────────────────────────
可在 accuracy_evaluator.py 中調整:
• similarity_threshold: 相似度閾值 (預設 0.8)
• weight_config: 各欄位的權重設定
• 文字標準化規則

🔧 進階使用
────────────────────────────────────────────────────────────────────────────────
如需處理特殊格式的資料，可以:
1. 修改 smart_processor.py 中的欄位映射邏輯
2. 調整 accuracy_evaluator.py 中的文字標準化函數
3. 自訂評估權重和閾值

📞 技術支援
────────────────────────────────────────────────────────────────────────────────
如遇到問題，請檢查:
1. Excel檔案格式是否正確
2. 是否有必要的Python套件 (pandas, numpy, openpyxl)
3. 檔案路徑和權限設定

🎯 最佳實踐
────────────────────────────────────────────────────────────────────────────────
• 確保測試資料的品質和一致性
• 定期備份評估結果
• 根據實際需求調整評估參數
• 結合人工檢查驗證自動評估結果
"""
    
    print(guide)


def generate_summary_report():
    """生成系統使用總結報告"""
    
    print("\n" + "="*80)
    print("系統執行總結報告")
    print("="*80)
    
    # 檢查工作目錄中的檔案
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
    result_files = [f for f in os.listdir('.') if f.startswith('智能評估結果_') and f.endswith('.xlsx')]
    
    print(f"📁 工作目錄: {os.getcwd()}")
    print(f"📊 Excel檔案數量: {len(excel_files)}")
    print(f"📋 評估結果檔案: {len(result_files)}")
    
    if excel_files:
        print(f"\n📂 輸入檔案:")
        for i, file in enumerate(excel_files, 1):
            file_size = os.path.getsize(file) / 1024  # KB
            print(f"  {i}. {file} ({file_size:.1f} KB)")
    
    if result_files:
        print(f"\n📈 輸出結果:")
        for i, file in enumerate(result_files, 1):
            file_size = os.path.getsize(file) / 1024  # KB
            print(f"  {i}. {file} ({file_size:.1f} KB)")
    
    # 如果有最新的評估結果，顯示摘要
    if result_files:
        latest_result = max(result_files, key=os.path.getctime)
        print(f"\n📊 最新評估結果: {latest_result}")
        
        try:
            df = pd.read_excel(latest_result, sheet_name='摘要')
            print(f"\n準確度摘要:")
            for _, row in df.iterrows():
                print(f"  • {row['欄位名稱']}: {row['準確度']} (匹配率: {row['匹配率']})")
        except Exception as e:
            print(f"  無法讀取摘要資料: {e}")
    
    print(f"\n✅ 系統運行正常，所有功能已就緒")
    print(f"🚀 使用方式:")
    print(f"   1. 準備Excel檔案")
    print(f"   2. 執行: python smart_processor.py")
    print(f"   3. 查看結果檔案")


def main():
    """主程式"""
    print_usage_guide()
    generate_summary_report()


if __name__ == "__main__":
    main()
