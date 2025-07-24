# How to Use

All you need to do is barely run the python script mcp_server.py to initiate the API service and get the url which can be integrate into Dify.

## How to Make Modifiication

### Change output structure in Dify: just change it in this return:
```python
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
```
### Add or drop some information in "result":
```python
        # 格式化结构化结果
        formatted = []
        for i, item in enumerate(results, 1):
            if item.get("score", 0) >= 0.600:
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
```

## Author

**David Qu**  
Undergraduate Researcher | AI Algorithm Engineer  
University of Toronto Scarborough - Department of Computer Science  
📧 davidsz.qu@mail.utoronto.ca