from qdrant_client import AsyncQdrantClient, models

from app.conf.app_config import app_config
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


class ColumnQdrantRepository:
    collection_name = 'column_collection'
    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def upsert_column_vectors(self,ids: list[str],vectors: list[list[float]],payloads: list[ColumnInfoQdrant]):
        # 如果column_collection集合不存在时，创建集合（实际使用）
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

        # 批量插入向量的数据：
        # 多个vector的列表：vectors: list[list[float]]
        # 多个payload的列表：payloads: list[包含字段信息的dict]
        # 多个id的列表：ids: list[str]

        # 一次性插入全部向量，很耗时甚至崩溃
        # await self.client.upsert(
        #     collection_name=self.collection_name,
        #     points=[
        #         models.PointStruct(
        #             id=ids[i],
        #             vector=vectors[i],
        #             payload=payloads[i]
        #         )
        #         for i in range(len(ids))
        #     ],
        # )

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


    async def search(self, vector: list[float])->list[ColumnInfoQdrant]:
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
        # 将payload字典转成ColumnInfoQdrant对象
        return [ColumnInfoQdrant(**point.payload) for point in result.points]
