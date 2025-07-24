# Introduction

## Localized Pipeline for PubMed Knowledge Base Construction

This repository implements a 5-stage pipeline that transforms raw PubMed data into a vectorized and searchable Milvus database. The goal is to support efficient biomedical literature retrieval and downstream LLM-based question answering systems (RAG).

### 🔁 Overview: Five-Stage Pipeline
[1] Batch Retrieval of PMIDs (via EDirect)\
↓\
[2] Download Article Details (efetch + xtract)\
↓\
[3] Clean and Structure into JSON\
↓\
[4] Embedding Generation (via API)\
↓\
[5] Insert into Milvus Vector Database\

---

### 🧾 Stage 1: Retrieve Large-Scale PMIDs via EDirect

Use NCBI EDirect tools to query PubMed:

```bash
esearch -db pubmed -query "rare disease AND 2015:2025[dp]" | \
efetch -format uid > pmid.txt
```

### 📄 Stage 2: Fetch Article Details (XML Format)
Split the PMIDs into manageable batches and fetch metadata:
```bash
split -l 1000 pmid.txt pmid_batch_
./fetch_pubmed_batches.sh
```

### 🧪 Stage 3: Convert XML to Structured JSON
Transform XML files into clean, structured JSON for downstream use:
```bash
python parse_pubmed_xml_batch_robust.py
```

### 🧠 Stage 4: Generate Embeddings
Embed the article titles and abstracts into vector representations:
```bash
python generate_embeding.py
```
Embedding model can be self-hosted or accessed via OpenAI-compatible APIs.

### 🗃️ Stage 5: Insert into Milvus Vector Database
Store all JSON entries into a Milvus collection for vector-based search:
```bash
python store_jsons_to_milvus.py
```

## Author
**David Qu**  
Undergraduate Researcher | AI Algorithm Engineer  
University of Toronto Scarborough - Department of Computer Science  
📧 davidsz.qu@mail.utoronto.ca