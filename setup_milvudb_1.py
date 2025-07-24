from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection

# 1. 连接本地 Milvus
connections.connect("default", host="localhost", port="19530")

# 2. 定义字段
fields = [
    FieldSchema(name="pmid", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=32),
    FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="abstract", dtype=DataType.VARCHAR, max_length=15000),
    FieldSchema(name="doi", dtype=DataType.VARCHAR, max_length=128),
    FieldSchema(name="authors", dtype=DataType.VARCHAR, max_length=5000),   # 有些文献作者非常多，也需要扩展成max_length = 10000
    FieldSchema(name="journal", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="year", dtype=DataType.VARCHAR, max_length=10),        
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
]

# 3. 定义 schema
schema = CollectionSchema(fields=fields, description="Rare disease literature from PubMed")

# 4. 创建 Collection
collection = Collection(name="pubmed_rare_disease_db", schema=schema)

# 5. 创建索引
collection.create_index(
    field_name="embedding",
    index_params={"index_type": "IVF_FLAT", "metric_type": "COSINE", "params": {"nlist": 128}}
)

# 6. 加载进内存
collection.load()
