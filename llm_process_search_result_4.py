import os
import requests
import json
from search_milvusdb_3 import search_pubmed_by_query

# ====== 模型配置读取 ======
LLM_API_BASE = os.getenv("LLM_BINDING_HOST", "http://localhost:18081/v1")
LLM_API_KEY = os.getenv("LLM_BINDING_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen3-32B")
USE_TRANSLATION = True  # 如果为 True，尝试将输出翻译为中文

# ====== 构造 Prompt ======
def build_prompt(docs, user_query):
    prompt = f"""You are a medical research assistant. Based on the following PubMed articles retrieved in response to the query: "{user_query}", summarize the key findings, patterns, and any notable observations in 500 words or less.

    Return your summary in Chinese with well-structured bullet points or a concise paragraph. 你的回答应使用中文/no_think。

    ### Articles:
    """
    for i, doc in enumerate(docs, 1):
        prompt += f"""
                    --- Article {i} ---
                    Title: {doc['title']}
                    Authors: {doc['authors']}
                    DOI: {doc['doi']}
                    Abstract: {doc['abstract']}
                """
    return prompt.strip()

# ====== 调用本地大模型 (OpenAI API 兼容方式) ======
# def summarize_with_llm(prompt):
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {LLM_API_KEY}"
#     }

#     payload = {
#         "model": LLM_MODEL,
#         "messages": [
#             {"role": "system", "content": "You are a helpful assistant for summarizing medical research, and also give the source articals' title, author names, Journal and year."},
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.7,
#         "enable_thinking": False,
#         # "stream": True
#     }

#     try:
#         response = requests.post(f"{LLM_API_BASE}/chat/completions", headers=headers, data=json.dumps(payload))
#         response.raise_for_status()
#         output = response.json()
#         return output["choices"][0]["message"]["content"]
#     except requests.exceptions.RequestException as e:
#         print("❌ 请求失败:", str(e))
#         return None
#     except KeyError:
#         print("❌ 响应格式异常: ", response.text)
#         return None

def summarize_with_llm(prompt: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system",
             "content": "You are a helpful assistant for summarizing medical research, "
                        "and also give the source articles' title, author names, "
                        "Journal and year."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "stream": True,            # 打开流式
        "extra_body": {"enable_thinking": False}   # 关闭思考链（商业版默认 False）
    }

    resp = requests.post(
        f"{LLM_API_BASE}/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        stream=True,             
        timeout=160
    )
    resp.raise_for_status()

    full_content = ""
    for raw_line in resp.iter_lines(decode_unicode=True):
        # SSE 数据格式：data: {...}  或  data: [DONE]
        if not raw_line or raw_line == "data: [DONE]":
            continue
        if raw_line.startswith("data: "):
            try:
                data = json.loads(raw_line[6:])
                delta = data["choices"][0]["delta"]
                if delta.get("content"):
                    piece = delta["content"]
                    full_content += piece
                    print(piece, end="", flush=True)
            except Exception as e:
                print(f"[解析错误] {e}")
    return full_content

# ====== 翻译函数（使用 prompt 翻译） ======
# def translate_to_chinese(text):
#     prompt = f"请将以下英文医学内容翻译成简洁准确的中文：\n\n{text}"
#     return summarize_with_llm(prompt)

# ====== 主执行入口 ======
def main():
    user_query = input("请输入你的研究问题或关键词：\n> ").strip()
    print("\n🔍 正在检索相关文献...")

    # 这里模拟检索结果（你应替换为实际 Milvus 检索调用）
    top_articles = search_pubmed_by_query(user_query)
    if not top_articles:
        print("未找到相关文章。")
        return
        
    print(f"\n✅ 找到 {len(top_articles )} 篇相关文章，正在整理中...\n")
    prompt = build_prompt(top_articles, user_query)
    
    summary = summarize_with_llm(prompt)
    if summary is None:
        print("❌ 无法生成总结。")
        return

    # print("\n📄 思考与总结如下：\n")
    # print(summary)

    # if USE_TRANSLATION:
    #     print("\n🌐 正在翻译为中文...\n")
    #     translated = translate_to_chinese(summary)
    #     print("\n📄 中文翻译如下：\n")
    #     print(translated if translated else "⚠️ 翻译失败。")

if __name__ == "__main__":
    main()
