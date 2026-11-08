import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.context import DataAgentContext
from app.agent.graph import graph
from app.agent.state import DataAgentState
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class QueryService:
    def __init__(
            self,
            value_es_repo: ValueEsRepository,
            dw_mysql_repo: DWMysqlRepository,
            meta_mysql_repo: MetaMysqlRepository,
            column_qdrant_repo: ColumnQdrantRepository,
            metric_qdrant_repo: MetricQdrantRepository,
            embedding_client: HuggingFaceEndpointEmbeddings,
    ):
        self.value_es_repo = value_es_repo
        self.dw_mysql_repo = dw_mysql_repo
        self.meta_mysql_repo = meta_mysql_repo
        self.column_qdrant_repo = column_qdrant_repo
        self.metric_qdrant_repo = metric_qdrant_repo
        self.embedding_client = embedding_client

    async def search(self, query: str):
        try:
            # 创建上下文对象
            context = DataAgentContext(
                dw_mysql_repo=self.dw_mysql_repo,
                meta_mysql_repo=self.meta_mysql_repo,
                value_es_repo=self.value_es_repo,
                column_qdrant_repo=self.column_qdrant_repo,
                metric_qdrant_repo=self.metric_qdrant_repo,
                embedding_client=self.embedding_client
            )

            # 创建状态对象
            state = DataAgentState(query=query)

            # 异步流式执行图
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                # print(chunk) # {"stage":"xx"} or {"result":[{},{},...]}
                # 返回结果给前端（转成json字符串）
                # ensure_ascii=False 不要转成ascii码
                # default=str 不能转成json的对象默认转为str
                yield f'data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n'

        except Exception as e:
            # 返回错误给前端
            yield f'data: {json.dumps({"error": str(e)}, ensure_ascii=False, default=str)}\n\n'
