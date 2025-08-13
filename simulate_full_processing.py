#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate the full multi-model processing pipeline
模擬完整的多模型處理流程
"""

import pandas as pd
import sys
import os
import io

# 添加api目錄到路徑
sys.path.append('api')

def simulate_full_processing():
    """模擬完整的多模型處理流程"""
    
    print("=" * 60)
    print("模擬完整的多模型處理流程")
    print("=" * 60)
    
    test_file = "data/multi_model_test_proper.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 測試檔案不存在: {test_file}")
        return
    
    # 步驟1: 讀取檔案內容
    print("📊 步驟1: 讀取檔案內容")
    with open(test_file, 'rb') as f:
        file_content = f.read()
    print(f"檔案大小: {len(file_content)} bytes")
    
    # 步驟2: 模擬 _read_excel_from_memory
    print(f"\n📊 步驟2: 模擬 _read_excel_from_memory")
    df = read_excel_from_memory(file_content)
    
    if df is None:
        print("❌ 無法讀取Excel檔案")
        return
    
    print(f"讀取結果: {len(df)} 行 x {len(df.columns)} 欄")
    
    # 步驟3: 模擬模型分割
    print(f"\n📊 步驟3: 模擬模型分割")
    model_blocks = split_models_from_dataframe(df)
    
    if not model_blocks:
        print("❌ 沒有找到任何模型")
        return
    
    print(f"找到 {len(model_blocks)} 個模型: {list(model_blocks.keys())}")
    
    # 步驟4: 模擬每個模型的處理
    print(f"\n📊 步驟4: 模擬每個模型的處理")
    
    successful_models = 0
    
    for model_name, model_df in model_blocks.items():
        print(f"\n🔍 處理模型: {model_name}")
        print(f"  資料大小: {len(model_df)} 行 x {len(model_df.columns)} 欄")
        
        try:
            # 模擬欄位驗證
            mappings = validate_and_map_columns(model_df)
            
            if mappings:
                print(f"  ✅ 欄位驗證成功: {mappings}")
                
                # 模擬評估過程
                print(f"  🔄 模擬評估過程...")
                
                # 檢查資料品質
                data_quality_ok = check_data_quality(model_df, mappings)
                
                if data_quality_ok:
                    print(f"  ✅ 資料品質檢查通過")
                    successful_models += 1
                else:
                    print(f"  ❌ 資料品質檢查失敗")
                    
            else:
                print(f"  ❌ 欄位驗證失敗")
                
        except Exception as e:
            print(f"  ❌ 處理失敗: {e}")
    
    # 總結
    print(f"\n📊 處理總結:")
    print(f"總模型數: {len(model_blocks)}")
    print(f"成功處理: {successful_models}")
    print(f"失敗數量: {len(model_blocks) - successful_models}")
    
    if successful_models > 0:
        print(f"✅ 多模型處理應該成功")
    else:
        print(f"❌ 所有模型都處理失敗")

def read_excel_from_memory(file_content: bytes):
    """模擬 _read_excel_from_memory 方法"""
    
    try:
        # 首先嘗試讀取完整的原始資料（header=None）來檢查是否為多模型檔案
        file_buffer = io.BytesIO(file_content)
        raw_df = pd.read_excel(file_buffer, engine='openpyxl', header=None)
        
        # 檢查是否包含多個模型
        model_count = 0
        for idx, row in raw_df.iterrows():
            row_values = [str(cell).strip() if pd.notna(cell) else '' for cell in row]
            for cell_value in row_values:
                if cell_value:
                    cell_lower = cell_value.lower()
                    model_keywords = ['gemini', 'gemma', 'chatgpt', 'claude', 'gpt', 'llama', 'palm', 'bard']
                    if any(keyword in cell_lower for keyword in model_keywords):
                        model_count += 1
                        break
        
        print(f"偵測到 {model_count} 個模型名稱")
        
        # 如果偵測到多個模型，返回原始資料（header=None）
        if model_count > 1:
            print("偵測到多模型檔案，使用原始資料格式")
            return raw_df
        
        print("偵測到單模型檔案，使用智能標題偵測")
        # 這裡可以加入單模型的處理邏輯
        return raw_df
        
    except Exception as e:
        print(f"讀取Excel檔案失敗: {e}")
        return None

def split_models_from_dataframe(df: pd.DataFrame):
    """模擬模型分割邏輯"""
    
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

def validate_and_map_columns(df: pd.DataFrame):
    """模擬欄位驗證和映射"""
    
    columns = list(df.columns)
    mappings = {}
    
    # 尋找障礙等級欄位
    disability_level_cols = []
    for i, col in enumerate(columns):
        col_str = str(col).strip()
        if '障礙等級' in col_str:
            disability_level_cols.append((i, col))
    
    # 尋找障礙類別欄位
    disability_category_cols = []
    for i, col in enumerate(columns):
        col_str = str(col).strip()
        if '障礙類別' in col_str:
            disability_category_cols.append((i, col))
    
    # 尋找ICD診斷欄位
    icd_diagnosis_cols = []
    for i, col in enumerate(columns):
        col_str = str(col).strip()
        if 'ICD診斷' in col_str or 'ICD' in col_str:
            icd_diagnosis_cols.append((i, col))
    
    # 根據位置判斷正面(正確答案)和反面(AI預測)
    if len(disability_level_cols) >= 2:
        correct_col = disability_level_cols[0][1]
        predicted_col = disability_level_cols[1][1]
        mappings['障礙等級'] = (correct_col, predicted_col)
    
    if len(disability_category_cols) >= 2:
        correct_col = disability_category_cols[0][1]
        predicted_col = disability_category_cols[1][1]
        mappings['障礙類別'] = (correct_col, predicted_col)
    
    if len(icd_diagnosis_cols) >= 2:
        correct_col = icd_diagnosis_cols[0][1]
        predicted_col = icd_diagnosis_cols[1][1]
        mappings['ICD診斷'] = (correct_col, predicted_col)
    
    # 如果找到至少2個映射，認為驗證成功
    if len(mappings) >= 2:
        return mappings
    
    return None

def check_data_quality(df: pd.DataFrame, mappings: dict):
    """檢查資料品質"""
    
    for field_name, (correct_col, predicted_col) in mappings.items():
        # 檢查欄位是否存在
        if correct_col not in df.columns or predicted_col not in df.columns:
            print(f"    ❌ 欄位不存在: {correct_col} 或 {predicted_col}")
            return False
        
        # 檢查是否有資料
        correct_data = df[correct_col].dropna()
        predicted_data = df[predicted_col].dropna()
        
        if len(correct_data) == 0 or len(predicted_data) == 0:
            print(f"    ❌ 欄位 {field_name} 沒有有效資料")
            return False
    
    return True

if __name__ == "__main__":
    simulate_full_processing()
