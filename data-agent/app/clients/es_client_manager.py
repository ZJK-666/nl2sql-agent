import asyncio
from elasticsearch import AsyncElasticsearch
from app.conf.app_config import ESConfig, app_config

# 操作ES的客户端管理器类
class ESClientManager:
    # 初始化实例属性
    def __init__(self, config: ESConfig):
        self.config = config
        self.client: AsyncElasticsearch | None = None

    # 获取连接的URL
    def _get_url(self):
        return f'http://{self.config.host}:{self.config.port}'

    # 初始化客户端
    def init(self):
        self.client = AsyncElasticsearch(self._get_url())

    # 关闭管理器，释放资源
    async def close(self):
        await self.client.close()

# 创建ES客户端管理器
es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':
    async def test():
        # 初始化客户端
        es_client_manager.init()
        # 获取客户端
        client = es_client_manager.client

        # 如果test_index存在则删除（测试）
        if await client.indices.exists(index="test_index"):
            await client.indices.delete(index="test_index")

        # 创建index
        await client.indices.create(
            index="test_index",
            mappings={
                "dynamic": False,
                "properties": {
                    "name": {
                        "type": "text"
                    },
                    "author": {
                        "type": "text"
                    },
                    "release_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "page_count": {
                        "type": "integer"
                    }
                }
            },
        )

        # 批量插入文档
        await client.bulk(
            operations=[
                {
                    "index": {
                        "_index": "test_index"
                    }
                },
                {
                    "name": "Revelation Space",
                    "author": "Alastair Reynolds",
                    "release_date": "2000-03-15",
                    "page_count": 585
                },
                {
                    "index": {
                        "_index": "test_index"
                    }
                },
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1985-06-01",
                    "page_count": 328
                },
                {
                    "index": {
                        "_index": "test_index"
                    }
                },
                {
                    "name": "Fahrenheit 451",
                    "author": "Ray Bradbury",
                    "release_date": "1953-10-15",
                    "page_count": 227
                },
                {
                    "index": {
                        "_index": "test_index"
                    }
                },
                {
                    "name": "Brave New World",
                    "author": "Aldous Huxley",
                    "release_date": "1932-06-01",
                    "page_count": 268
                },
                {
                    "index": {
                        "_index": "test_index"
                    }
                },
                {
                    "name": "The Handmaids Tale",
                    "author": "Margaret Atwood",
                    "release_date": "1985-06-01",
                    "page_count": 311
                }
            ],
            # refresh=True # 自动刷新保存数据
        )

        # 1.执行插入文档后，并不会马上写入ES，数据在ES缓存区，需要1秒后才会存入数据
        # await asyncio.sleep(1)
        # 2.可以在插入文档时配置自动刷新保存数据，每插入一个文档刷新一次（效率低）
        # refresh = True
        # 3.手动刷新保存数据（实际项目中不需要，因为添加数据和查询是分开的）
        await client.indices.refresh(index='test_index')

        # 搜索
        result = await client.search(
            index="test_index",
            query={ # 设置搜索条件
                "match": { # 设置要匹配的键和值
                    "name": "brave"
                }
            },
        )
        print(result["hits"]["hits"][0]['_source'])

        # 关闭管理器，释放资源
        await es_client_manager.close()

    # 执行协程
    asyncio.run(test())
