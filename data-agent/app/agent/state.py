from typing import TypedDict

from app.models.es.value_info_es import ValueInfoEs
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant

class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list

class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]

class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str

class DBInfoState(TypedDict):
    version: str
    dialect: str

# 自定义State的模型（类型）存可变数据
class DataAgentState(TypedDict):
    """Agent的状态数据"""
    query: str # 用户的提问
    keywords: list[str] # 提问分词后的列表
    error: str # 校验sql的错误信息
    recall_columns: list[ColumnInfoQdrant] # 召回的字段信息列表
    recall_metrics: list[MetricInfoQdrant] # 召回的指标信息列表
    recall_values: list[ValueInfoEs] # 召回的字段取值列表
    table_infos: list[TableInfoState] # 合并后的表及字段信息列表
    metric_infos: list[MetricInfoState] # 合并后的指标信息列表
    date_info: DateInfoState # 日期时间信息
    db_info: DBInfoState # 数据库信息
    sql: str # 大模型生成的sql
