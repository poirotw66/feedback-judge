#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify the structure of the generated Excel output file
驗證生成的Excel輸出檔案結構
"""

import pandas as pd
import os

def verify_excel_structure(filename: str = "gemma3_result.xlsx"):
    """驗證Excel檔案結構"""
    
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在: {filename}")
        return False
    
    print("=" * 60)
    print(f"驗證Excel檔案結構: {filename}")
    print("=" * 60)
    
    try:
        # 讀取Excel檔案的所有工作表
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        
        print(f"📊 工作表數量: {len(sheet_names)}")
        print(f"📋 工作表名稱: {sheet_names}")
        print()
        
        # 檢查每個工作表的內容
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"{i}. 【{sheet_name}】")
            
            try:
                df = pd.read_excel(filename, sheet_name=sheet_name)
                print(f"   📏 大小: {len(df)} 行 x {len(df.columns)} 欄")
                print(f"   📝 欄位: {list(df.columns)}")
                
                # 顯示前幾行資料預覽
                if len(df) > 0:
                    print(f"   👀 資料預覽:")
                    for idx, row in df.head(3).iterrows():
                        row_preview = " | ".join([f"{col}={str(val)[:20]}..." if len(str(val)) > 20 else f"{col}={val}" for col, val in row.items()[:3]])
                        print(f"      行{idx+1}: {row_preview}")
                
                print()
                
            except Exception as e:
                print(f"   ❌ 讀取失敗: {e}")
                print()
        
        # 特別檢查新增的工作表
        print("🔍 檢查新增的詳細分析工作表:")
        
        # 檢查個別記錄分析
        if '個別記錄分析' in sheet_names:
            print("✅ 個別記錄分析工作表存在")
            df_individual = pd.read_excel(filename, sheet_name='個別記錄分析')
            
            # 統計受編數量
            unique_subjects = df_individual[df_individual['受編'] != '']['受編'].nunique()
            print(f"   📊 包含 {unique_subjects} 個受編的詳細分析")
            
            # 檢查是否有正解、模型識別結果等欄位
            required_columns = ['受編', '欄位', '正解', '模型識別結果', '準確度', '狀態']
            missing_columns = [col for col in required_columns if col not in df_individual.columns]
            if not missing_columns:
                print("   ✅ 包含所有必要欄位")
            else:
                print(f"   ❌ 缺少欄位: {missing_columns}")
        else:
            print("❌ 個別記錄分析工作表不存在")
        
        # 檢查欄位準確度摘要
        if '欄位準確度摘要' in sheet_names:
            print("✅ 欄位準確度摘要工作表存在")
            df_field_summary = pd.read_excel(filename, sheet_name='欄位準確度摘要')
            
            print(f"   📊 包含 {len(df_field_summary)} 個欄位的準確度統計")
            
            # 檢查欄位準確度資訊
            if '整體準確度' in df_field_summary.columns:
                print("   ✅ 包含整體準確度資訊")
                for _, row in df_field_summary.iterrows():
                    field_name = row['欄位名稱']
                    accuracy = row['整體準確度']
                    match_rate = row.get('完全匹配率', 'N/A')
                    print(f"      {field_name}: {accuracy} (匹配率: {match_rate})")
            else:
                print("   ❌ 缺少整體準確度欄位")
        else:
            print("❌ 欄位準確度摘要工作表不存在")
        
        print()
        print("🎉 Excel檔案結構驗證完成！")
        return True
        
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

def show_sample_individual_records(filename: str = "gemma3_result.xlsx", num_records: int = 2):
    """顯示個別記錄分析的範例"""
    
    try:
        df = pd.read_excel(filename, sheet_name='個別記錄分析')
        
        print("=" * 60)
        print("個別記錄分析範例")
        print("=" * 60)
        
        current_subject = None
        record_count = 0
        
        for _, row in df.iterrows():
            if record_count >= num_records:
                break
                
            if row['受編'] and row['受編'] != current_subject:
                current_subject = row['受編']
                record_count += 1
                print(f"\n受編: {current_subject}")
                print(f"  {row['狀態']} ({row['備註']})")
                continue
            
            if row['欄位'] and row['欄位'] not in ['=== 記錄開始 ===', '--- 分隔線 ---']:
                field_name = row['欄位']
                correct = row['正解']
                predicted = row['模型識別結果']
                accuracy = row['準確度']
                status = row['狀態']
                
                print(f"  {field_name}: 正解=\"{correct}\", 模型識別=\"{predicted}\", 準確度={accuracy}")
                print(f"    狀態: {status}")
        
    except Exception as e:
        print(f"❌ 顯示範例時發生錯誤: {e}")

if __name__ == "__main__":
    # 驗證檔案結構
    success = verify_excel_structure()
    
    if success:
        print()
        # 顯示個別記錄分析範例
        show_sample_individual_records()
    
    print("\n📋 檔案驗證完成！")
