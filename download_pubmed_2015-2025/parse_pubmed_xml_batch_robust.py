import os
import json
import xml.etree.ElementTree as ET
from tqdm import tqdm

INPUT_FOLDER = "xml_batches"
OUTPUT_FOLDER = "json_batches"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def parse_article(article) -> dict:
    try:
        medline = article.find("MedlineCitation")
        pmid = medline.findtext("PMID", default="")

        article_data = medline.find("Article")
        title = article_data.findtext("ArticleTitle", default="")

        abstract_e = article_data.find("Abstract")
        abstract_parts = [t.text for t in abstract_e.findall("AbstractText")] if abstract_e is not None else []
        abstract = " ".join(p for p in abstract_parts if p)

        author_list = article_data.find("AuthorList")
        authors = []
        if author_list is not None:
            for author in author_list.findall("Author"):
                fn = author.findtext("ForeName")
                ln = author.findtext("LastName")
                if fn and ln:
                    authors.append(f"{fn} {ln}")

        doi = ""
        for eloc in article_data.findall("ELocationID"):
            if eloc.attrib.get("EIdType") == "doi":
                doi = eloc.text
                break

        journal = article_data.find("Journal")
        journal_title = journal.findtext("Title", default="") if journal is not None else ""

        pub_year = journal.find("JournalIssue").find("PubDate").findtext("Year", default="") if journal is not None else ""

        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": ", ".join(authors),
            "doi": doi,
            "journal": journal_title,
            "year": pub_year,
            "source": "PubMed"
        }
    except Exception as e:
        print(f"⚠️ 单篇解析失败: {e}")
        return None


def process_batch_file_safe(file_path: str, output_path: str):
    results = []
    try:
        context = ET.iterparse(file_path, events=("end",))
        for event, elem in context:
            if elem.tag == "PubmedArticle":
                parsed = parse_article(elem)
                if parsed:
                    results.append(parsed)
                elem.clear()  # 节省内存
    except ET.ParseError as e:
        print(f"⚠️ 文件部分解析失败: {file_path} - {e}")

    if results:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ 完成解析 {file_path}，成功提取 {len(results)} 篇")
    else:
        print(f"🚫 无有效文章提取于 {file_path}")


def process_all_batches():
    xml_files = sorted(f for f in os.listdir(INPUT_FOLDER) if f.endswith(".xml"))

    for file in tqdm(xml_files, desc="📦 正在解析 XML 批次"):
        input_path = os.path.join(INPUT_FOLDER, file)
        output_path = os.path.join(OUTPUT_FOLDER, file.replace(".xml", ".json"))

        if os.path.exists(output_path):
            continue  # 避免重复处理

        process_batch_file_safe(input_path, output_path)


if __name__ == "__main__":
    process_all_batches()
