from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, TableInfoState, ColumnInfoState, MetricInfoState
from app.core.log import logger
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant


# 节点：合并召回信息
async def merge_recall(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 输出给前端的数据（前后端约定好的数据格式）
    runtime.stream_writer({"stage":"合并召回信息"})

    # recall_columns: list[ColumnInfoQdrant] # 召回的字段信息列表
    # recall_metrics: list[MetricInfoQdrant] # 召回的指标信息列表
    # recall_values: list[ValueInfoEs] # 召回的字段取值列表
    recall_columns = state["recall_columns"]
    recall_metrics = state["recall_metrics"]
    recall_values = state["recall_values"]
    meta_mysql_repo = runtime.context['meta_mysql_repo']

    # 最终的数据：
    table_infos: list[TableInfoState] = []
    metric_infos: list[MetricInfoState] = []

    # 1.收集完整的字段信息列表
    # 1.1主要来源是 recall_columns
    # {column_id: ColumnInfoQdrant对象}
    column_infos_dict: dict[str,ColumnInfoQdrant] = {column['id']: column for column in recall_columns}

    # 1.2补充：召回指标关联的字段
    for metric in recall_metrics:
        for column_id in metric['relevant_columns']:
            if column_id not in column_infos_dict:
                column_info_mysql: ColumnInfoMySQL = await meta_mysql_repo.get_column_info_by_id(column_id)
                column_infos_dict[column_id] = _convert_column_info_mysql_to_qdrant(column_info_mysql)

    # 1.3补充：召回字段值对应的字段，还要将字段值添加到 examples 中
    for value_info in recall_values:
        column_id = value_info['column_id']
        if column_id not in column_infos_dict:
            column_info_mysql: ColumnInfoMySQL = await meta_mysql_repo.get_column_info_by_id(column_id)
            column_infos_dict[column_id] = _convert_column_info_mysql_to_qdrant(column_info_mysql)
        if value_info['value'] not in column_infos_dict[column_id]['examples']:
            column_infos_dict[column_id]['examples'].append(value_info['value'])

    logger.info(f'column_infos_dict: {column_infos_dict}')


    # 1.4对字段信息列表按表分组：{table_id: list[ColumnInfoQdrant]}
    table_columns_dict: dict[str, list[ColumnInfoQdrant]] = {}
    for column_info in column_infos_dict.values():
        table_id = column_info['table_id']
        if table_id not in table_columns_dict:
            table_columns_dict[table_id] = []
        table_columns_dict[table_id].append(column_info)

    logger.info(f'table_columns_dict: {table_columns_dict}')


    # 1.5补充：相关表的主外键字段
    for table_id,column_list in table_columns_dict.items():
        # 去meta库查当前表的主键和外键的字段信息
        key_column_infos: list[ColumnInfoMySQL] = await meta_mysql_repo.get_column_infos_by_table_id(table_id)
        for key_column_info in key_column_infos:
            # 将主外键的字段信息转成ColumnInfoQdrant对象
            key_column_info_qdrant = _convert_column_info_mysql_to_qdrant(key_column_info)
            if key_column_info.id not in column_infos_dict:
                # 当前主外键字段的id如果不在column_infos_dict中
                # 那么肯定不在 table_columns_dict 中的某个列表里
                # 因为 table_columns_dict 是根据 column_infos_dict 生成的
                table_columns_dict[table_id].append(key_column_info_qdrant)

        # 2.生成TableInfoState对象的列表
        # 2.1查询table_info表得到指定id的表信息
        table_info_mysql: TableInfoMySQL = await meta_mysql_repo.get_table_info_by_id(table_id)
        # 2.2创建ColumnInfoState对象列表
        columns: list[ColumnInfoState] = [_convert_column_info_qdrant_to_state(column) for column in column_list]
        # 2.3创建TableInfoState对象
        table_info: TableInfoState = TableInfoState(
            name=table_info_mysql.name,
            role=table_info_mysql.role,
            description=table_info_mysql.description,
            columns=columns
        )
        # 2.4生成TableInfoState对象列表
        table_infos.append(table_info)

    logger.info(f'合并召回表信息: {table_infos}')

    # 3.创建MetricInfoState对象的列表
    metric_infos: list[MetricInfoState] = [
        _convert_metric_info_qdrant_to_state(recall_metric)
        for recall_metric in recall_metrics
    ]
    logger.info(f"合并召回指标信息:{metric_infos}")

    return {"table_infos": table_infos, "metric_infos": metric_infos}


def _convert_column_info_qdrant_to_state(column:ColumnInfoQdrant)->ColumnInfoState:
    return ColumnInfoState(
        name=column['name'],
        type=column['type'],
        role=column["role"],
        examples=column["examples"],
        description=column["description"],
        alias=column["alias"]
    )


def _convert_metric_info_qdrant_to_state(recall_metric:MetricInfoQdrant)->MetricInfoState:
    return MetricInfoState(
        name=recall_metric['name'],
        description=recall_metric["description"],
        relevant_columns=recall_metric["relevant_columns"],
        alias=recall_metric["alias"]
    )


def _convert_column_info_mysql_to_qdrant(column_info_mysql:ColumnInfoMySQL)->ColumnInfoQdrant:
    return ColumnInfoQdrant(
        id=column_info_mysql.id,
        name=column_info_mysql.name,
        description=column_info_mysql.description,
        role=column_info_mysql.role,
        type=column_info_mysql.type,
        examples=column_info_mysql.examples,
        alias=column_info_mysql.alias,
        table_id = column_info_mysql.table_id
    )
