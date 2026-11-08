from elasticsearch import AsyncElasticsearch

from app.clients.es_client_manager import es_client_manager
from app.models.es.value_info_es import ValueInfoEs


class ValueEsRepository:
    index_name = "value_index"
    mappings = { # 索引映射结构
        "dynamic": False, # 关闭动态映射
        "properties": { # 文档的属性，定义文档中的字段及类型
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word"},
            "type": {"type": "keyword"},
            "column_id": {"type": "keyword"},
            "column_name": {"type": "keyword"},
            "table_id": {"type": "keyword"},
            "table_name": {"type": "keyword"},
        }
    }
    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    # 批量插入多个字段信息
    async def insert_values(self, values: list[ValueInfoEs]):
        # 初始化客户端
        es_client_manager.init()
        # 获取客户端
        client = es_client_manager.client

        # 如果value_index存在则删除（测试用）
        if await client.indices.exists(index=self.index_name):
            await client.indices.delete(index=self.index_name)
        # 创建index
        await client.indices.create(
            index=self.index_name,
            mappings=self.mappings
        )

        # 如果value_index不存在则创建（生产用）
        # if not await client.indices.exists(index=self.index_name):
        #     # 创建index
        #     await client.indices.create(
        #         index=self.index_name,
        #         mappings=self.mappings
        #     )

        # 批量插入文档
        # await client.bulk(
        #     operations=[ # 一个文档包含一个item1和item2
        #         { # item1
        #             "index": {
        #                 "_index": self.index_name,
        #             }
        #         },
        #         { # item2 -> ValueInfoEs对象
        #             "name": "Revelation Space",
        #             "author": "Alastair Reynolds",
        #             "release_date": "2000-03-15",
        #             "page_count": 585
        #         },
        #     ],
        # )

        operations = []
        item1 = {
            "index": {
                "_index": self.index_name,
            }
        }
        for item2 in values:
            operations.append(item1)
            operations.append(item2)

        # 批量插入文档（一次性插入所有数据，效率低，容易崩溃）
        # await client.bulk(operations=operations)

        # 分批插入文档
        batch_size = 20 # 每次插入10个文档
        for i in range(0, len(operations), batch_size):
            batch_operations = operations[i:i+batch_size]
            await client.bulk(operations=batch_operations)

    # 搜索字段值信息
    async def search(self, keyword:str, threshold:float=0.6, limit:int=5)->list[ValueInfoEs]:
        result = await self.client.search(
            index=self.index_name,
            query={  # 设置搜索条件
                "match": {  # 设置要匹配的键和值
                    "value": keyword
                }
            },
            size=limit, # 设置返回结果的数量
            min_score=threshold, # 设置返回结果的最小得分
        )
        # print(result["hits"]["hits"][0]['_source'])
        # 读取文档数据并整理为ValueInfoEs对象列表
        return [ValueInfoEs(**item["_source"]) for item in result["hits"]["hits"]]

