import uuid

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.meta_config import MetaConfig, TableConfig, MetricConfig
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoEs
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

# 构建元数据知识库的业务类
class MetaKnowledgeService:
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

    async def build(self, config: MetaConfig):
        # 构建元数据知识库的业务方法
        logger.info("构建业务 开始")
        # 调用repository中的方法

        # 1 处理表相关信息数据
        if config.tables:
            # 1.1 保存表信息到meta数据库(table_info表)
            column_infos: list[ColumnInfoMySQL] = await self._save_table_infos_to_meta(config.tables)
            logger.info('保存表信息到meta数据库')
            # 1.2 保存字段信息到meta数据库(column_info表)
            await self._save_column_infos_to_meta(column_infos)
            logger.info('保存字段信息到meta数据库')
            # 1.3 为字段信息建立向量索引
            await self._save_column_infos_to_qdrant(column_infos)
            logger.info('为字段信息建立向量索引')
            # 1.4 为字段取值建立全文索引
            await self._save_column_values_to_es(column_infos, config.tables)
            logger.info('为字段取值建立全文索引')

        # 2 处理指标信息数据
        if config.metrics:
            # 2.1 保存指标信息到meta数据库(metric_info表)
            metric_infos: list[MetricInfoMySQL] = await self._save_metric_infos_to_meta(config.metrics)
            logger.info('保存指标信息到meta数据库1')
            # 2.2 保存指标信息到meta数据库(column_metric表)
            await self._save_column_metric_to_meta(config.metrics)
            logger.info('保存指标信息到meta数据库2')
            # 2.3 为指标信息建立向量索引
            await self._save_metric_infos_to_qdrant(metric_infos)
            logger.info('为指标信息建立向量索引')

        logger.info("构建业务 完成")

    async def _save_table_infos_to_meta(self, tables: list[TableConfig])->list[ColumnInfoMySQL]:
        # 1.1 保存表信息到meta数据库(table_info表)

        table_infos: list[TableInfoMySQL] = []
        column_infos: list[ColumnInfoMySQL] = []

        # 1.遍历tables中所有表信息，封装成表信息对象的列表（table_infos）
        for table in tables:
            # 创建ORM对象
            table_info = TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description,
            )
            table_infos.append(table_info)

            # 查询dw库当前table中的所有字段数据类型 -> dict[字段名:字段数据类型]
            column_types: dict = await self.dw_mysql_repo.get_column_types(table.name)

            # 2.遍历当前表的字段信息，封装成字段信息对象的列表（column_infos）
            for column in table.columns:
                # 查询dw库取出指定字段的前10条数据
                column_values: list = await self.dw_mysql_repo.get_column_values(table.name, column.name, 10)

                # 创建ORM对象
                column_info = ColumnInfoMySQL(
                    id=f'{table.name}.{column.name}',
                    name=column.name,
                    type=column_types[column.name], # 需要查询获取，先放着
                    role=column.role,
                    examples=column_values, # 需要查询获取，先放着
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                )
                column_infos.append(column_info)

        # 3.调用持久层的方法保存到 table_info 表中
        self.meta_mysql_repo.save_table_infos(table_infos)

        # 4.返回字段信息对象的列表（column_infos）
        return column_infos


    async def _save_column_infos_to_meta(self, column_infos: list[ColumnInfoMySQL]):
        # 1.2 保存字段信息到meta数据库(column_info表)
        # 调用持久层的方法保存到 column_info 表中
        self.meta_mysql_repo.save_column_infos(column_infos)


    async def _save_column_infos_to_qdrant(self, column_infos: list[ColumnInfoMySQL]):
        # 遍历column_infos，对每个column_info中的name和description字段，及alias字段的每一个值进行向量化
        # 每一个向量point包含 id vector payload
        # vector 需要embedding向量化
        # 为每一个向量生成对应的id和payload（包含column_info中所有数据的字典对象）
        # 调用持久层方法保存到qdrant库中

        # 收集每个向量点的信息的字典列表
        # points = [{id:,embedding_text:,payload:},{}...]
        points: list[dict] = []
        # 遍历字段信息列表
        for column_info in column_infos:
            payload = ColumnInfoQdrant(
                id=column_info.id,
                name=column_info.name,
                type=column_info.type,
                role=column_info.role,
                examples=column_info.examples,
                description=column_info.description,
                alias=column_info.alias,
                table_id=column_info.table_id
            )
            # name字段
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.name,
                "payload": payload
            })
            # description字段
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": column_info.description,
                "payload": payload
            })
            # alias字段
            for alia in column_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": payload
                })

        # 获取所有向量文本
        embedding_texts = [point["embedding_text"] for point in points]
        # 每批向量化的数量
        batch_size = 10
        # 所有向量的列表
        vectors: list[list[float]] = []
        # 遍历所有向量文本
        for i in range(0, len(embedding_texts), batch_size):
            # 获取一批向量文本 list[str]
            batch_embedding_texts = embedding_texts[i:i + batch_size]
            # 转换一批向量 list[list[float]]
            batch_vectors = await self.embedding_client.aembed_documents(batch_embedding_texts)
            # 放入向量列表 list[list[float]]
            vectors.extend(batch_vectors)
            # vectors.append(batch_vectors) 不可以，多一层嵌套

        # 生成所有的 id
        ids = [point["id"] for point in points]
        # 生成所有的 payload
        payloads = [point["payload"] for point in points]

        # 保存字段数据到向量数据库
        await self.column_qdrant_repo.upsert_column_vectors(ids, vectors, payloads)


    async def _save_column_values_to_es(self, column_infos: list[ColumnInfoMySQL], tables: list[TableConfig]):
        # 为字段取值建立全文索引
        # 遍历column_infos，根据配置判断字段是否需要建立全文索引
        # 查询dw库取出需要建立全文索引的字段的所有值
        # 为每一个值创建ValueInfoEs对象，并添加到列表list[ValueInfoEs]中
        # 调用持久层方法保存到es库中

        # 1.收集配置中所有字段的sync：dict[column_id,bool]
        column_sync_dict: dict[str,bool] = {}
        for table in tables:
            for column in table.columns:
                column_sync_dict[f'{table.name}.{column.name}'] = column.sync

        value_infos: list[ValueInfoEs] = []
        # 2.遍历所有字段信息column_infos
        for column_info in column_infos:
            # 判断字段是否需要建立全文索引
            if column_sync_dict.get(column_info.id, False):
                # 查询dw库取出指定字段的所有值
                values = await self.dw_mysql_repo.get_column_values(column_info.table_id, column_info.name, 100000)
                # 遍历字段的所有值，创建ValueInfoEs对象，并添加到列表中
                for value in values:
                    value_infos.append(ValueInfoEs(
                        id=f'{column_info.id}.{value}', # 需要生成唯一id
                        value=value, # 字段取值
                        type=column_info.type, # 字段类型
                        column_id=column_info.id, # 字段id
                        column_name=column_info.name, # 字段名称
                        table_id=column_info.table_id, # 表id
                        table_name=column_info.table_id, # 表名称
                    ))
        # 3.调用持久层方法保存到es库中
        await self.value_es_repo.insert_values(value_infos)


    async def _save_metric_infos_to_meta(self, metrics: list[MetricConfig])->list[MetricInfoMySQL]:
        # 保存指标信息到meta数据库(metric_info表)
        metric_infos: list[MetricInfoMySQL] = []
        for metric in metrics:
            metric_infos.append(MetricInfoMySQL(
                id=metric.name,
                name=metric.name,
                description=metric.description,
                relevant_columns=metric.relevant_columns,
                alias=metric.alias
            ))

        # 调用持久层方法保存到meta库中
        self.meta_mysql_repo.save_metric_infos(metric_infos)

        # 返回metric_infos，建立指标信息向量索引要用
        return metric_infos


    async def _save_column_metric_to_meta(self, metrics: list[MetricConfig]):
        # 保存指标信息到meta数据库(column_metric表)
        column_metrics: list[ColumnMetricMySQL] = []
        for metric in metrics:
            for column_id in metric.relevant_columns:
                column_metrics.append(ColumnMetricMySQL(
                    metric_id=metric.name,  # 指标id
                    column_id=column_id  # 字段id
                ))

        # 调用持久层方法保存到meta库中
        self.meta_mysql_repo.save_column_metrics(column_metrics)


    async def _save_metric_infos_to_qdrant(self, metric_infos: list[MetricInfoMySQL]):
        # 为指标信息建立向量索引
        # 遍历metric_infos，对每个metric_info中的name和description字段，及alias字段的每一个值进行向量化
        # 每一个向量point包含 id vector payload
        # vector 需要embedding向量化
        # 为每一个向量生成对应的id和payload（包含metric_info中所有数据的字典对象）
        # 调用持久层方法保存到qdrant库中

        # 收集每个向量点的信息的字典列表
        # points = [{id:,embedding_text:,payload:},{}...]
        points: list[dict] = []
        # 遍历字段信息列表
        for metric_info in metric_infos:
            payload = MetricInfoQdrant(
                id=metric_info.id,
                name=metric_info.name,
                description=metric_info.description,
                alias=metric_info.alias,
                relevant_columns=metric_info.relevant_columns
            )
            # name字段
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload": payload
            })
            # description字段
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload": payload
            })
            # alias字段
            for alia in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload": payload
                })

        # 获取所有向量文本
        embedding_texts = [point["embedding_text"] for point in points]
        # 每批向量化的数量
        batch_size = 10
        # 所有向量的列表
        vectors: list[list[float]] = []
        # 遍历所有向量文本
        for i in range(0, len(embedding_texts), batch_size):
            # 获取一批向量文本 list[str]
            batch_embedding_texts = embedding_texts[i:i + batch_size]
            # 转换一批向量 list[list[float]]
            batch_vectors = await self.embedding_client.aembed_documents(batch_embedding_texts)
            # 放入向量列表 list[list[float]]
            vectors.extend(batch_vectors)
            # vectors.append(batch_vectors) 不可以，多一层嵌套

        # 生成所有的 id
        ids = [point["id"] for point in points]
        # 生成所有的 payload
        payloads = [point["payload"] for point in points]

        # 保存指标数据到向量数据库
        await self.metric_qdrant_repo.upsert_metric_vectors(ids, vectors, payloads)





