#!/usr/bin/env python3
"""
MCP Server for PubMed Vector Search using FastMCP + httpx
"""

from fastmcp import FastMCP
import httpx
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from search_pubmed_by_query import search_pubmed_by_query 
from datetime import datetime

# 加载 .env 环境变量
load_dotenv()

# 初始化 MCP Server
server = FastMCP()

@server.tool()
async def search_pubmed_vector(
    query: str,
    top_k: int = 5,
    socre: float = 0.6,
) -> Dict[str, Any]:
    """
    从本地 Milvus 向量数据库中检索 PubMed 相关文献

    Args:
        query: 查询字符串，支持疾病、药物、症状、基因等
        top_k: 返回前多少个结果（默认5）

    Returns:
        包含自然语言摘要（text）和结构化检索结果（json）
    """

    if not query:
        raise Exception("请提供有效的查询关键词")

    try:
        # 调用已有检索函数
        results = search_pubmed_by_query(query=query, top_k=top_k)

        # 格式化结构化结果
        formatted = []
        for i, item in enumerate(results, 1):
            if item.get("score", 0) >= socre:
                formatted.append({
                    "rank": i,
                    "score": round(item.get("score", 0.0), 3),
                    "pmid": item.get("pmid", ""),
                    "title": item.get("title", ""),
                    # "doi": item.get("doi", ""),
                    # "authors": item.get("authors", []),
                    # "journal": item.get("journal", ""),
                    # "year": item.get("year", ""),
                    "abstract": item.get("abstract", "")
                })

        # 构造清晰的自然语言摘要
        summary_lines = [f"PubMed 检索关键词：{query}\n"]
        for i, item in enumerate(formatted, 1):
            summary_lines.append(f"{i}.《{item['title']}》")
            # summary_lines.append(f"  期刊: {item['journal']}（{item['year']}）")
            summary_lines.append(f"  PMID: {item['pmid']}")
            if item['abstract']:
                summary_lines.append(f" 摘要: {item['abstract']}" )
            summary_lines.append("")  # 空行分隔

        text_summary = "\n".join(summary_lines).strip()

        return {"query": query,
                "result": formatted,
                "text": text_summary,
                "metadata": {
                                "source": "local_pubmed_vector_db",
                                "retrieved_at": datetime.now(),
                                "top_k": top_k,
                                "tool": "search_pubmed_vector"
                            }
                }  # 给 LLM 使用


    except Exception as e:
        raise Exception(f"文献检索失败: {str(e)}")

# 启动 FastMCP Server（使用 HTTP 接口）
if __name__ == "__main__":
    server.run(transport="http", host="0.0.0.0", port=8035)

