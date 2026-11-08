from typing import TypedDict
# 数据模型
class MetricInfoQdrant(TypedDict):
    id:str
    name:str
    description:str
    relevant_columns:list
    alias:list
