import asyncio

from qdrant_client import AsyncQdrantClient, models

from app.conf.app_config import QdrantConfig, app_config


# 操作qdrant数据库的客户端管理器类
class QdrantClientManager:
    # 初始化实例属性
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client: AsyncQdrantClient | None = None

    # 获取连接的url
    def _get_url(self):
        return f'http://{self.config.host}:{self.config.port}'

    # 初始化客户端
    def init(self):
        self.client = AsyncQdrantClient(self._get_url())

    # 关闭管理器，释放资源
    async def close(self):
        await self.client.close()

# 创建qdrant客户端管理器
qdrant_client_manager = QdrantClientManager(app_config.qdrant)

# 测试qdrant操作
if __name__ == '__main__':
    async def test():
        # 初始化客户端
        qdrant_client_manager.init()
        # 获取客户端
        client = qdrant_client_manager.client

        # 如果my_collection集合不存在时，创建集合（实际使用）
        # if not await client.collection_exists(collection_name="my_collection"):
        #     # 异步创建集合
        #     await client.create_collection(
        #         # 集合名称
        #         collection_name="my_collection",
        #         # 向量配置
        #         vectors_config=models.VectorParams(
        #             size=4,  # 向量维度
        #             distance=models.Distance.COSINE  # 向量距离算法：余弦
        #         ),
        #     )

        # 如果my_collection集合已存在时，删除集合（测试使用）
        if await client.collection_exists(collection_name="my_collection"):
            await client.delete_collection(collection_name="my_collection")
        # 异步创建集合
        await client.create_collection(
            # 集合名称
            collection_name="my_collection",
            # 向量配置
            vectors_config=models.VectorParams(
                size=4, # 向量维度，app_config.yaml中有
                distance=models.Distance.COSINE # 向量距离算法：余弦
            ),
        )

        # 添加数据/修改数据
        await client.upsert(
            collection_name="my_collection",
            points=[
                models.PointStruct(id=1, vector=[0.05, 0.61, 0.76, 0.74], payload={"city": "Berlin","num": 1}),
                models.PointStruct(id=2, vector=[0.19, 0.81, 0.75, 0.11], payload={"city": "London","num": 2}),
                models.PointStruct(id=3, vector=[0.36, 0.55, 0.47, 0.94], payload={"city": "Moscow","num": 1}),
                models.PointStruct(id=4, vector=[0.18, 0.01, 0.85, 0.80], payload={"city": "New York","num": 2}),
                models.PointStruct(id=5, vector=[0.24, 0.18, 0.22, 0.44], payload={"city": "Beijing","num": 1}),
                models.PointStruct(id=6, vector=[0.35, 0.08, 0.11, 0.44], payload={"city": "Mumbai","num": 2}),
                models.PointStruct(id=7, vector=[0.9, 0.1, 0.1, 0.5], payload={"city": "Shenzhen","num": 1})
            ],
        )

        # 删除数据
        # result = await client.delete(
        #     collection_name="my_collection",
        #     points_selector=[1,3] # 删除id为1和3的Point
        # )
        # print(result.status) # completed 表示成功

        # 查询数据
        result = await client.query_points(
            collection_name="my_collection",
            query=[0.9, 0.1, 0.1, 0.5],
            limit=5, # 返回最相似的3个向量
            score_threshold=0.6, # 向量相似度阈值，低于该阈值的向量将被忽略
            query_filter=models.Filter( # 根据payload中的键和值来过滤
                must=[models.FieldCondition(key="num", match=models.MatchValue(value=1))]
            )
        )
        print(result.points) # [ScoredPoint,ScoredPoint,...]

        # 关闭管理器，释放资源
        await qdrant_client_manager.close()

    # 执行协程
    asyncio.run(test())