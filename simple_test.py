#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的多模型測試
"""

import sys
import os
sys.path.append('/Users/cfh00896102/Github/feedback-judge')

import pandas as pd
from api.evaluator_service import DisabilityDataEvaluatorService

def test_model_splitting():
    """測試模型分割功能"""
    print("測試模型分割功能...")
    
    # 創建測試資料
    test_data = [
        # 模型1
        ['gemini-2.5-pro', '', '', ''],
        ['編號', '受編', '障礙等級', '障礙類別'],
        [1, 'ZA001', '輕度', '其他類'],
        [2, 'ZA002', '中度', '第1類'],
        
        # 空行
        ['', '', '', ''],
        
        # 模型2
        ['gemma3:27b', '', '', ''],
        ['編號', '受編', '障礙等級', '障礙類別'],
        [1, 'ZA001', '中度', '第2類'],
        [2, 'ZA002', '輕度', '其他類'],
    ]
    
    df = pd.DataFrame(test_data, columns=['col1', 'col2', 'col3', 'col4'])
    
    # 測試分割
    service = DisabilityDataEvaluatorService()
    model_blocks = service.split_models_from_dataframe(df)
    
    print(f"找到 {len(model_blocks)} 個模型:")
    for model_name, model_df in model_blocks.items():
        print(f"  模型: {model_name}")
        print(f"  資料筆數: {len(model_df)}")
        print(f"  欄位: {list(model_df.columns)}")
        print("  預覽:")
        print(model_df.head())
        print("-" * 40)
    
    return len(model_blocks) > 1

if __name__ == "__main__":
    try:
        success = test_model_splitting()
        if success:
            print("✅ 模型分割測試成功!")
        else:
            print("❌ 模型分割測試失敗!")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
