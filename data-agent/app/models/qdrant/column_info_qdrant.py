from typing import TypedDict
# TypedDict 是 Python 在 typing 模块中提供的一个实用工具，
# 专门用来解决普通字典在类型提示上的不足，让你能为字典的“结构”做出清晰的定义。

# 简单来说，普通字典（dict）的类型提示通常很宽泛，
# 比如 dict[str, int] 表示所有键都是字符串，所有值都是整数。
# 但它的局限性在于，无法指定具体有哪些键，以及每个键对应的值类型是什么。
# TypedDict 正是为此而生。

# 定义qdrant中保存的字段信息的模型
class ColumnInfoQdrant(TypedDict):
    id: str
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list
    table_id: str
