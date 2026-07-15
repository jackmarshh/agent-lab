import chromadb
from chromadb.utils import embedding_functions
import os

# --- 1. 分块策略 (Chunking Strategy) ---
def split_text(text: str, chunk_size: int = 150, overlap: int = 30):
    """
    模拟递归字符切分逻辑：
    - chunk_size: 每个块的最大字符数
    - overlap: 相邻块之间的重叠字数，保证语义连贯
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # 步进 = 大小 - 重叠
        start += (chunk_size - overlap)
    return chunks

def ingest():
    db_path = os.path.join(os.getcwd(), "my_vectordb")
    client = chromadb.PersistentClient(path=db_path)
    
    # 使用支持中文的多语言模型
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    
    # 每次运行前先删除旧集合，确保实验干净
    try:
        client.delete_collection("travel_guides")
    except:
        pass
    collection = client.create_collection(name="travel_guides", embedding_function=emb_fn)

    # --- 2. 模拟长文档数据 ---
    raw_documents = [
        {
            "city": "三亚",
            "content": "三亚后海村是年轻人的冲浪天堂，这里有非常多的冲浪店。如果你是初学者，建议找一个教练带。晚上的沙滩派对非常热闹，有很多年轻人聚在一起喝酒听音乐。此外，后海村的物价相对亚龙湾要亲民很多，适合长期居住。"
        },
        {
            "city": "三亚",
            "content": "亚龙湾的海水是三亚最清澈的，沙质也非常细腻。这里分布着很多高端度假酒店，非常适合家庭亲子游。如果你想安安静静地晒太阳，亚龙湾是首选。需要注意的是，这里的消费较高，建议提前在网上订好酒店套餐。"
        },
        {
            "city": "北京",
            "content": "故宫博物院是北京旅游的必经之地。目前故宫实行全面预约制，必须提前7天在官方公众号预约。周一全天闭馆，请规划好时间。建议从午门进入，沿着中轴线参观，最后从神武门出，对面就是景山公园，可以俯瞰故宫全景。"
        }
    ]

    # --- 3. 执行分块并打标签 (Metadata) ---
    all_chunks = []
    all_metadatas = []
    all_ids = []
    
    counter = 0
    for doc in raw_documents:
        chunks = split_text(doc["content"])
        for chunk in chunks:
            all_chunks.append(chunk)
            # 这里的 metadata 是混合检索的关键：它可以让搜索时限定城市
            all_metadatas.append({"city": doc["city"]})
            all_ids.append(f"id_{counter}")
            counter += 1

    print(f"✅ 文档已切分为 {len(all_chunks)} 个 Chunk，并带有元数据标签。")
    
    # 4. 存入数据库
    collection.add(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )
    print("🚀 向量数据库已重构完成。")

if __name__ == "__main__":
    ingest()
