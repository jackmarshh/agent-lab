from app.models import Evidence


def get_weather(city: str) -> list[Evidence]:
    """模拟查询天气工具"""
    # 模拟逻辑：如果是三亚就晴天，如果是其他地方就模拟小雨
    if "三亚" in city:
        detail = "天气晴朗，气温 30°C，紫外线强，非常适合海滩活动。"
    elif "北京" in city:
        detail = "晴间多云，气温 22°C，风力 3 级，体感舒适。"
    else:
        detail = f"{city} 当前多云转小雨，气温 15°C，建议携带雨具。"
    return [Evidence(source="天气预报中心", detail=detail)]


def get_flight_price(city: str) -> list[Evidence]:
    """模拟查询机票价格工具"""
    # 模拟逻辑：不同城市的机票价格
    if "三亚" in city:
        prices = [
            Evidence(source="携程机票", detail=f"前往 {city} 的机票当前特价：￥1200"),
            Evidence(source="南方航空", detail=f"前往 {city} 的机票全价：￥2800")
        ]
    else:
        prices = [
            Evidence(source="去哪儿网", detail=f"前往 {city} 的机票均价：￥800"),
        ]
    return prices


import chromadb
from chromadb.utils import embedding_functions
import os

def search_knowledge(query: str, city_filter: str = None) -> list[Evidence]:
    """真正的 RAG 工具：使用 ChromaDB 进行混合检索（语义搜索 + 元数据过滤）"""
    db_path = os.path.join(os.getcwd(), "my_vectordb")
    
    if not os.path.exists(db_path):
        return [Evidence(source="向量库", detail="向量数据库尚未初始化，请运行 ingest_data.py")]

    try:
        # 1. 连接本地库
        client = chromadb.PersistentClient(path=db_path)
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        collection = client.get_collection(name="travel_guides", embedding_function=emb_fn)

        # 2. 执行混合检索
        # where 子句实现了 Metadata Filtering (元数据过滤)，这就是“混合”的关键
        search_params = {
            "query_texts": [query],
            "n_results": 2
        }
        if city_filter:
            search_params["where"] = {"city": city_filter}

        results = collection.query(**search_params)

        evidence_list = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                evidence_list.append(Evidence(
                    source=f"向量库({metadata['city']})", 
                    detail=doc
                ))
        else:
            evidence_list.append(Evidence(source="向量库", detail=f"未找到与 '{query}' 相关的深度攻略。"))
        
        return evidence_list
    except Exception as e:
        return [Evidence(source="向量库错误", detail=f"检索失败: {str(e)}")]

def get_local_food(city: str) -> list[Evidence]:
    """模拟查询当地美食工具"""
    if "三亚" in city:
        detail = "推荐美食：清补凉、文昌鸡、和乐蟹。三亚海鲜市场目前价格透明，评价极高。"
    elif "北京" in city:
        detail = "推荐美食：北京烤鸭、老北京炸酱面。近期各大烤鸭店需提前预约。"
    else:
        detail = f"当地美食：{city} 特色小吃，建议在大众点评查看实时榜单。"
    
    return [Evidence(source="大众点评/美食百科", detail=detail)]
