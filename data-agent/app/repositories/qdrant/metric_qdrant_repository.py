from qdrant_client import AsyncQdrantClient, models

from app.conf.app_config import app_config
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


class MetricQdrantRepository:
    collection_name = 'metric_collection'
    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def upsert_metric_vectors(self,ids: list[str],vectors: list[list[float]],payloads: list[MetricInfoQdrant]):
        # 如果metric_collection集合不存在时，创建集合
        if not await self.client.collection_exists(collection_name=self.collection_name):
            # 异步创建集合
            await self.client.create_collection(
                # 集合名称
                collection_name=self.collection_name,
                # 向量配置
                vectors_config=models.VectorParams(
                    size=app_config.qdrant.embedding_size, # 向量维度
                    distance=models.Distance.COSINE # 向量距离算法：余弦
                ),
            )

        # 分批插入多个向量
        batch_size = 10
        for i in range(0, len(ids), batch_size):
            # 获取批量数据
            batch_ids = ids[i:i+batch_size]
            batch_vectors = vectors[i:i+batch_size]
            batch_payloads = payloads[i:i+batch_size]
            # 插入批量数据
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=batch_ids[n],
                        vector=batch_vectors[n],
                        payload=batch_payloads[n]
                    )
                    for n in range(len(batch_ids))
                ],
            )


    async def search(self, vector: list[float]) -> list[MetricInfoQdrant]:
        # 查询数据
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            # limit=5,  # 返回最相似的5个向量,默认10
            score_threshold=0.6,  # 向量相似度阈值，低于该阈值的向量将被忽略
        )
        # print(result.points)  # [ScoredPoint,ScoredPoint,...]

        # 返回查询结果
        # 此时,payload是纯字典,不是想要的类型
        # return [point.payload for point in result.points]
        # 将payload字典转成MetricInfoQdrant对象
        return [MetricInfoQdrant(**point.payload) for point in result.points]
