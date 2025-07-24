import os
import time
import requests
from typing import List, Dict
from pymilvus import Collection, connections
from Bio import Entrez
from dotenv import load_dotenv

# ================= 配置区 =================
load_dotenv()
ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL")
ENTREZ_API_KEY = os.getenv("ENTREZ_API_KEY")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_DIM = 1024
SLEEP_INTERVAL = 0.2
SEARCH_BATCH_SIZE = 100
FETCH_BATCH_SIZE = 100

Entrez.email = ENTREZ_EMAIL
Entrez.api_key = ENTREZ_API_KEY
PUBMED_COLLECTION_NAME = "pubmed_rare_disease_db"

# ============ 获取近期PMID列表 ============
def fetch_pubmed_ids_recent_days(query: str, days: int = 30, retmax: int = 100) -> List[str]:
    initial = Entrez.esearch(
        db="pubmed",
        term=query,
        reldate=days,
        datetype="pdat",
        retmax=0,
        usehistory="y",
        retmode="xml"
    )
    record = Entrez.read(initial)
    initial.close()

    total_count = int(record["Count"])
    webenv = record["WebEnv"]
    query_key = record["QueryKey"]
    print(f"📊 PubMed中最近 {days} 天共找到 {total_count} 篇文献")

    all_pmids = []
    for start in range(0, total_count, retmax):
        print(f"🔍 拉取第 {start} - {min(start + retmax, total_count)} 条PMID")
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            reldate=days,
            datetype="pdat",
            retstart=start,
            retmax=retmax,
            usehistory="y",
            webenv=webenv,
            query_key=query_key,
            retmode="xml"
        )
        batch = Entrez.read(handle)
        handle.close()
        all_pmids.extend(batch["IdList"])
        time.sleep(SLEEP_INTERVAL)

    print(f"✅ 共成功获取 {len(all_pmids)} 条PMID")
    return all_pmids

# ============ 获取特定年份范围内的PMID列表 ============
# def fetch_pubmed_ids_by_year_range(query: str, mindate: str = "2015", maxdate: str = "2025", retmax: int = 100) -> List[str]:
#     initial = Entrez.esearch(
#         db="pubmed",
#         term=query,
#         datetype="pdat",
#         mindate=mindate,
#         maxdate=maxdate,
#         retmax=0,
#         usehistory="y",
#         retmode="xml"
#     )
#     record = Entrez.read(initial)
#     initial.close()

#     total_count = int(record["Count"])
#     webenv = record["WebEnv"]
#     query_key = record["QueryKey"]
#     print(f"📊 PubMed中从 {mindate} 到 {maxdate} 共找到 {total_count} 篇文献")

#     all_pmids = []
#     for start in range(0, total_count, retmax):
#         print(f"🔍 拉取第 {start} - {min(start + retmax, total_count)} 条PMID")
#         handle = Entrez.esearch(
#             db="pubmed",
#             term=query,
#             datetype="pdat",
#             mindate=mindate,
#             maxdate=maxdate,
#             retstart=start,
#             retmax=retmax,
#             usehistory="y",
#             webenv=webenv,
#             query_key=query_key,
#             retmode="xml"
#         )
#         batch = Entrez.read(handle)
#         handle.close()
#         all_pmids.extend(batch["IdList"])
#         time.sleep(SLEEP_INTERVAL)

#     print(f"✅ 共成功获取 {len(all_pmids)} 条PMID")
#     return all_pmids

# ============ 获取详细文献信息 ============
def fetch_pubmed_details(pmids: List[str], batch_size: int = 100, sleep_time: float = 0.5) -> List[Dict]:
    results = []
    for i in range(0, len(pmids), batch_size):
        batch_pmids = pmids[i:i + batch_size]
        print(f"📥 获取文献详情: {i} - {i + len(batch_pmids)}")
        try:
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(batch_pmids),
                rettype="medline",
                retmode="xml"
            )
            records = Entrez.read(handle)
            handle.close()
        except Exception as e:
            print(f"❌ 批次失败: {e}")
            continue

        for article in records.get("PubmedArticle", []):
            try:
                medline = article["MedlineCitation"]
                article_data = medline["Article"]
                pmid = str(medline["PMID"])
                title = article_data.get("ArticleTitle", "")
                abstract_parts = article_data.get("Abstract", {}).get("AbstractText", [])
                abstract = " ".join(str(p) for p in abstract_parts) if abstract_parts else ""
                authors = [
                    f"{a['ForeName']} {a['LastName']}"
                    for a in article_data.get("AuthorList", [])
                    if "ForeName" in a and "LastName" in a
                ]
                doi = ""
                for id_ in article_data.get("ELocationID", []):
                    if id_.attributes.get("EIdType") == "doi":
                        doi = str(id_)
                        break
                journal = article_data.get("Journal", {}).get("Title", "")
                pub_year = article_data.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {}).get("Year", "")

                results.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": ", ".join(authors),
                    "doi": doi,
                    "journal": journal,
                    "year": pub_year,
                    "source": "PubMed"
                })
            except Exception as e:
                print(f"⚠️ 单篇解析失败: {e}")
                continue
        time.sleep(sleep_time)
    print(f"✅ 获取完毕，总共 {len(results)} 篇")
    return results

# ============ 嵌入模型调用 ============
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

# ============ 插入 Milvus ============
def insert_to_milvus(collection: Collection, docs: List[Dict]):
    if not docs:
        return
    print(f"📦 插入 Milvus：共 {len(docs)} 篇")
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
    print("✅ 插入完成")

# ============ 主流程 ============
def main():
    connections.connect()
    collection = Collection(PUBMED_COLLECTION_NAME)
    
    pmids = fetch_pubmed_ids_recent_days(query="rare disease",days=30, retmax=SEARCH_BATCH_SIZE)
    records = fetch_pubmed_details(pmids, batch_size=FETCH_BATCH_SIZE, sleep_time=SLEEP_INTERVAL)

    for i in range(0, len(records), 100):
        batch = records[i:i+100]
        for doc in batch:
            text = f"{doc['title']} {doc['abstract']}"
            try:
                doc["embedding"] = get_embedding(text)
            except Exception as e:
                print(f"❌ Embedding 失败: {doc['pmid']}: {e}")
                doc["embedding"] = [0.0] * EMBEDDING_DIM  # 填充空向量避免插入错误
        insert_to_milvus(collection, batch)

if __name__ == "__main__":
    main()
