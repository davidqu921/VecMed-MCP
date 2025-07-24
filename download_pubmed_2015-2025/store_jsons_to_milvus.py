import os
import json
from pymilvus import connections, Collection
from tqdm import tqdm
from dotenv import load_dotenv

# 配置 
load_dotenv()
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EMBEDDED_JSON_FOLDER = "json_embedded"

# ✅ 连接 Milvus
connections.connect("default", host="localhost", port="19530")
collection = Collection(COLLECTION_NAME)
collection.load()

def insert_to_milvus(docs):
    if not docs:
        return
    entities = [
        [doc["pmid"] for doc in docs],
        [doc["title"] for doc in docs],
        [doc["abstract"] for doc in docs],
        [doc["doi"] for doc in docs],
        [doc["authors"] for doc in docs],
        [doc["journal"] for doc in docs],
        [doc["year"] for doc in docs],
        [doc["source"] for doc in docs],
        [doc["embedding"] for doc in docs],
    ]
    collection.insert(entities)
    collection.flush()

# ✅ 遍历所有 JSON 文件
for filename in tqdm(sorted(os.listdir(EMBEDDED_JSON_FOLDER))):
    if not filename.endswith(".json"):
        continue
    file_path = os.path.join(EMBEDDED_JSON_FOLDER, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            print(f"⚠️ 文件格式错误：{filename}")
            continue

        valid_docs = []
        for item in data:
            try:
                # 检查是否包含所有字段
                required_fields = ["pmid", "title", "abstract", "doi", "authors",
                                   "journal", "year", "source", "embedding"]
                if all(k in item for k in required_fields):
                    valid_docs.append(item)
                else:
                    print(f"⚠️ 缺字段: {item.get('pmid', 'unknown')} in {filename}")
            except Exception as e:
                print(f"⚠️ 解析失败: {e}")
                continue

        if valid_docs:
            insert_to_milvus(valid_docs)
            print(f"✅ 已导入文件: {filename} 共 {len(valid_docs)} 条记录")
        else:
            print(f"⚠️ 无有效记录: {filename}")

    except Exception as e:
        print(f"❌ 文件处理失败: {filename}, 错误: {e}")
