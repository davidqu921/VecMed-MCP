import os
from pymilvus import MilvusClient
from typing import List, Dict
import requests
from dotenv import load_dotenv

# ==== 配置 ====
load_dotenv()
MILVUS_URI = os.getenv("MILVUS_URI")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EMBEDDING_DIM = 1024
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# ==== 初始化客户端 ====
client = MilvusClient(uri=MILVUS_URI)

# ==== 生成 embedding ====
def get_embedding(text: str) -> List[float]:
    payload = {
        "input": [text],
        "model": EMBEDDING_MODEL
    }
    response = requests.post(EMBEDDING_API_URL, json=payload)
    response.raise_for_status()
    embedding = response.json()["data"][0]["embedding"]
    if len(embedding) != EMBEDDING_DIM:
        raise ValueError(f"Embedding dim mismatch: {len(embedding)} != {EMBEDDING_DIM}")
    return embedding

# ==== Milvus 向量检索 ====
def search_in_milvus(query_vector: List[float], top_k: int = 5) -> List[Dict]:
    try:
        print(f"🔍 正在 Milvus 中搜索 Top-{top_k} 向量...")
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            data=[query_vector],
            search_params={
                "metric_type": "COSINE",
                "params": {"nprobe": 1}
            },
            limit=top_k,
            output_fields=["pmid", "title", "abstract", "doi", "authors", "journal", "year", "source"],
            consistency_level="Bounded"
        )
        results = []
        for hit in search_result[0]:  # 第一条 query 的结果
            entity = hit["entity"]
            results.append({
                "pmid": entity.get("pmid"),
                "title": entity.get("title"),
                "abstract": entity.get("abstract"),
                "doi": entity.get("doi"),
                "authors": entity.get("authors"),
                "journal": entity.get("journal"),
                "year": entity.get("year"),
                "source": entity.get("source"),
                "score": hit.get("distance")
            })

        print(f"✅ 检索完成，找到 {len(results)} 篇相关文献。")
        return results

    except Exception as e:
        raise RuntimeError(f"[ERROR] Milvus 向量检索失败: {e}")

# ==== 高层封装：从文本到搜索结果 ====
def search_pubmed_by_query(query: str, top_k: int = 3) -> List[Dict]:
    print(f"\n🎯 开始检索: \"{query}\"")
    query_vector = get_embedding(query)
    return search_in_milvus(query_vector, top_k=top_k)

# ==== 示例运行 ====
if __name__ == "__main__":
    example_query = "Multiple molecular diagnoses identified through genome sequencing in individuals with suspected rare disease."
    results = search_pubmed_by_query(example_query, top_k=3)

    for idx, item in enumerate(results, 1):
        print(f"\n🔸 Rank {idx} (score={item['score']:.4f})")
        print(f"PMID: {item['pmid']}")
        print(f"Title: {item['title']}")
        print(f"DOI: {item['doi']}")
        print(f"Authors: {', '.join(item['authors']) if isinstance(item['authors'], list) else item['authors']}")
        print(f"Journal: {item['journal']} ({item['year']})")
        print(f"Abstract: {item['abstract'][:300]}...")
