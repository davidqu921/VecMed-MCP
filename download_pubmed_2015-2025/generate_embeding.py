import os
import json
import time
import requests
from typing import List
from dotenv import load_dotenv


# ==== 配置 ====
load_dotenv()
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_DIM = 1024

INPUT_FOLDER = "json_batches"
OUTPUT_FOLDER = "json_embedded"
SLEEP_INTERVAL = 0.5  # 可调

# === 向量化函数 ===
def get_embedding(text: str) -> List[float]:
    payload = {
        "input": [text],
        "model": EMBEDDING_MODEL
    }
    try:
        response = requests.post(EMBEDDING_API_URL, json=payload)
        response.raise_for_status()
        embedding = response.json()["data"][0]["embedding"]
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(f"Embedding dim mismatch: got {len(embedding)}, expected {EMBEDDING_DIM}")
        return embedding
    except Exception as e:
        print(f"❌ 向量化失败: {e}")
        return []

# === 处理单个JSON文件 ===
def process_json_file(input_path: str, output_path: str):
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        print(f"❌ 读取失败: {input_path}, 错误: {e}")
        return

    new_records = []
    for record in records:
        try:
            combined = f"{record.get('title', '')} {record.get('abstract', '')}".strip()
            embedding = get_embedding(combined)
            if not embedding:
                continue
            record["embedding"] = embedding
            new_records.append(record)
            # time.sleep(SLEEP_INTERVAL)
        except Exception as e:
            print(f"⚠️ 单条失败: {e}")
            continue

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(new_records, f, ensure_ascii=False, indent=2)
        print(f"✅ 已处理: {input_path} → {output_path}, 共 {len(new_records)} 条")
    except Exception as e:
        print(f"❌ 写入失败: {output_path}, 错误: {e}")

# === 遍历所有文件 ===
def process_all_files():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    files = sorted(f for f in os.listdir(INPUT_FOLDER) if f.endswith(".json"))
    print(f"📁 待处理文件数: {len(files)}")

    for fname in files:
        in_path = os.path.join(INPUT_FOLDER, fname)
        out_path = os.path.join(OUTPUT_FOLDER, fname)
        process_json_file(in_path, out_path)

# === 执行入口 ===
if __name__ == "__main__":
    process_all_files()
