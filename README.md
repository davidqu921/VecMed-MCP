# Instruction
These files are aimed to establish a Milvus Vector Database

## What are those file used for?
0. docker-compose.yml: used for initiate MilvusDB
1. setup_milvus.py : formulate the schame of database.
2. download_pubmed_tomilvusdb.py: used for timely update, currently days=30.
3. search_milvusdb.py: only a test of searching function in MilvusDB.
4. llm_process_search_result.py: a experiment of trying to summarize search result using a LLM.
5. updating_milvusdb.log: record the updating operation.

## Current ATTU WebUI
See all the data on web, manage the collection, schame. No password needed.
Currently, the collection "pubmed_rare_disease_db" has more than 160k data from Pebmed related to rare disease.

## Environment Configuration
### Launch the docker-compose.yml
docker compose up -d

### MCP Tools Preparation
pip install marshmallow==3.20.1 -i https://pypi.tuna.tsinghua.edu.cn/simple\
pip install Flask -i https://pypi.tuna.tsinghua.edu.cn/simple\
pip install pymilvus -U -i https://pypi.tuna.tsinghua.edu.cn/simple\
pip install "mcp[cli]" -i https://pypi.tuna.tsinghua.edu.cn/simple\

### Attu WebUI Docker Setup
docker pull zilliz/attu:v2.4.4
docker run -d --name attu   -p 8000:3000   -e MILVUS_URL=192.168.10.199:19530   zilliz/attu:v2.4.4

![Attu](./graph/attu.png)


## Timer Update the Database
To add a new timer operation: crontab -e
To view to timer: crontab -l

## Author

**David Qu**  
Undergraduate Researcher | AI Algorithm Engineer  
University of Toronto Scarborough - Department of Computer Science  
📧 davidsz.qu@mail.utoronto.ca