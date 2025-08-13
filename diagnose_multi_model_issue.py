#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose multi-model processing issues
診斷多模型處理問題
"""

import pandas as pd
import sys
import os

# 添加api目錄到路徑
sys.path.append('api')

def diagnose_multi_model_processing():
    """診斷多模型處理問題"""
    
    print("=" * 60)
    print("診斷多模型處理問題")
    print("=" * 60)
    
    test_file = "data/multi_model_test_proper.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 測試檔案不存在: {test_file}")
        return
    
    # 步驟1: 讀取Excel檔案
    print("📊 步驟1: 讀取Excel檔案")
    try:
        # 嘗試不同的header設定
        for header_row in range(5):
            try:
                df = pd.read_excel(test_file, header=header_row)
                print(f"  header={header_row}: {len(df)} 行 x {len(df.columns)} 欄")
                print(f"    欄位: {list(df.columns)[:5]}...")
                
                # 檢查是否有有意義的欄位名稱
                meaningful_columns = 0
                has_key_fields = False
                
                for col in df.columns:
                    if isinstance(col, str) and not col.startswith('Unnamed'):
                        if any(keyword in str(col) for keyword in ['編號', '受編', '障礙', '類別', 'ICD', '備註']):
                            meaningful_columns += 1
                        
                        # 特別檢查是否有關鍵欄位組合
                        if '編號' in str(col) and '受編' in str(df.columns):
                            has_key_fields = True
                
                print(f"    有意義欄位數: {meaningful_columns}, 關鍵欄位: {has_key_fields}")
                
                if has_key_fields and meaningful_columns >= 4:
                    print(f"  ✅ 選擇 header={header_row}")
                    selected_df = df
                    break
                    
            except Exception as e:
                print(f"  header={header_row}: 讀取失敗 - {e}")
        else:
            print("  ❌ 無法找到合適的header設定")
            return
            
    except Exception as e:
        print(f"❌ 讀取Excel檔案失敗: {e}")
        return
    
    # 步驟2: 模型分割
    print(f"\n📊 步驟2: 模型分割")
    print(f"原始資料: {len(selected_df)} 行 x {len(selected_df.columns)} 欄")
    
    # 顯示前10行
    print(f"前10行內容:")
    for i in range(min(10, len(selected_df))):
        row_data = []
        for j in range(min(5, len(selected_df.columns))):
            cell_value = str(selected_df.iloc[i, j]) if pd.notna(selected_df.iloc[i, j]) else '[空]'
            row_data.append(cell_value[:15])  # 限制長度
        print(f"  行{i+1}: {row_data}")
    
    # 執行模型分割
    model_blocks = split_models_from_dataframe(selected_df)
    
    print(f"\n🔍 模型分割結果:")
    print(f"找到 {len(model_blocks)} 個模型: {list(model_blocks.keys())}")
    
    # 步驟3: 檢查每個模型的資料
    print(f"\n📊 步驟3: 檢查每個模型的資料")
    
    for model_name, model_df in model_blocks.items():
        print(f"\n📋 模型: {model_name}")
        print(f"  資料大小: {len(model_df)} 行 x {len(model_df.columns)} 欄")
        print(f"  欄位: {list(model_df.columns)}")
        
        # 檢查欄位映射
        print(f"  欄位分析:")
        
        # 尋找障礙等級欄位
        disability_level_cols = []
        for i, col in enumerate(model_df.columns):
            col_str = str(col).strip()
            if '障礙等級' in col_str:
                disability_level_cols.append((i, col))
        print(f"    障礙等級欄位: {disability_level_cols}")
        
        # 尋找障礙類別欄位
        disability_category_cols = []
        for i, col in enumerate(model_df.columns):
            col_str = str(col).strip()
            if '障礙類別' in col_str:
                disability_category_cols.append((i, col))
        print(f"    障礙類別欄位: {disability_category_cols}")
        
        # 尋找ICD診斷欄位
        icd_diagnosis_cols = []
        for i, col in enumerate(model_df.columns):
            col_str = str(col).strip()
            if 'ICD診斷' in col_str or 'ICD' in col_str:
                icd_diagnosis_cols.append((i, col))
        print(f"    ICD診斷欄位: {icd_diagnosis_cols}")
        
        # 檢查是否有足夠的欄位對
        mappings = {}
        if len(disability_level_cols) >= 2:
            mappings['障礙等級'] = (disability_level_cols[0][1], disability_level_cols[1][1])
        if len(disability_category_cols) >= 2:
            mappings['障礙類別'] = (disability_category_cols[0][1], disability_category_cols[1][1])
        if len(icd_diagnosis_cols) >= 2:
            mappings['ICD診斷'] = (icd_diagnosis_cols[0][1], icd_diagnosis_cols[1][1])
        
        print(f"    可能的映射: {mappings}")
        
        if len(mappings) >= 2:
            print(f"    ✅ 有足夠的欄位對進行評估")
        else:
            print(f"    ❌ 欄位對不足，無法進行評估")
        
        # 顯示前3行資料
        print(f"  前3行資料:")
        for i in range(min(3, len(model_df))):
            row_data = []
            for j in range(min(len(model_df.columns), 8)):  # 只顯示前8欄
                cell_value = str(model_df.iloc[i, j]) if pd.notna(model_df.iloc[i, j]) else '[空]'
                row_data.append(cell_value[:10])  # 限制長度
            print(f"    行{i+1}: {row_data}")

def split_models_from_dataframe(df: pd.DataFrame):
    """簡化版的模型分割邏輯"""
    
    model_blocks = {}
    current_model = None
    current_header_row = None
    block_rows = []
    
    for idx, row in df.iterrows():
        # 檢查每一行是否為模型名稱
        row_values = [str(cell).strip() if pd.notna(cell) else '' for cell in row]
        found_model = None
        
        # 檢查是否包含模型關鍵字
        for cell_value in row_values:
            if cell_value:
                cell_lower = cell_value.lower()
                model_keywords = ['gemini', 'gemma', 'chatgpt', 'claude', 'gpt', 'llama', 'palm', 'bard']
                if any(keyword in cell_lower for keyword in model_keywords):
                    found_model = cell_value
                    print(f"第 {idx + 1} 行發現模型名稱: {found_model}")
                    break
        
        if found_model:
            # 如果有前一個模型，儲存其 block
            if current_model and block_rows:
                if len(block_rows) > 0:
                    # 建立DataFrame，使用適當的header
                    if current_header_row is not None and len(block_rows) > 1:
                        # 使用找到的header行
                        model_df = pd.DataFrame(block_rows[1:], columns=block_rows[0])
                    else:
                        # 使用原始欄位名稱
                        model_df = pd.DataFrame(block_rows, columns=df.columns)
                    
                    # 過濾掉空行
                    model_df = model_df.dropna(how='all')
                    if len(model_df) > 0:
                        model_blocks[current_model] = model_df
                        print(f"模型 {current_model} 包含 {len(model_df)} 筆資料")
                
                block_rows = []
                current_header_row = None
            
            current_model = found_model
            continue
        
        # 檢查是否為header行（包含欄位關鍵字）
        if current_model and not current_header_row:
            header_keywords = ['編號', '受編', '障礙', '類別', 'ICD', '備註', '證明', '手冊']
            has_header_keywords = sum(1 for cell in row_values if any(keyword in str(cell) for keyword in header_keywords))
            
            if has_header_keywords >= 3:  # 至少包含3個關鍵字才認為是header
                current_header_row = idx
                block_rows.append(row_values)
                print(f"第 {idx + 1} 行被識別為模型 {current_model} 的header行")
                continue
        
        # 如果是資料行，加入目前模型的 block
        if current_model:
            # 檢查是否為有效的資料行（至少有一個非空值）
            if any(str(cell).strip() for cell in row_values if pd.notna(cell)):
                block_rows.append(row_values)
    
    # 處理最後一個模型
    if current_model and block_rows:
        if len(block_rows) > 0:
            if current_header_row is not None and len(block_rows) > 1:
                # 使用找到的header行
                model_df = pd.DataFrame(block_rows[1:], columns=block_rows[0])
            else:
                # 使用原始欄位名稱
                model_df = pd.DataFrame(block_rows, columns=df.columns)
            
            # 過濾掉空行
            model_df = model_df.dropna(how='all')
            if len(model_df) > 0:
                model_blocks[current_model] = model_df
                print(f"模型 {current_model} 包含 {len(model_df)} 筆資料")
    
    print(f"模型分割完成，總共找到 {len(model_blocks)} 個模型: {list(model_blocks.keys())}")
    return model_blocks

if __name__ == "__main__":
    diagnose_multi_model_processing()
