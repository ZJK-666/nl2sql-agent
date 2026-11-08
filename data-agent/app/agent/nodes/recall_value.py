from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoEs
from app.prompt.prompt_loader import load_prompt


# 节点：召回字段取值
async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 输出给前端的数据（前后端约定好的数据格式）
    runtime.stream_writer({"stage":"召回字段取值"})

    query = state["query"]
    keywords = state["keywords"]
    # 全文检索不需要向量
    # embedding_client = runtime.context["embedding_client"]
    value_es_repo = runtime.context["value_es_repo"]

    # 1.用大模型对query进行语义分词，并与jieba分词结果合并
    # 2.拿合并后的分词去做召回（关键字向量化）
    # 3.拿向量去查询qdrant向量库
    # 4.得到字段信息列表 list[MetricInfoQdrant]
    # 5.返回 list[MetricInfoQdrant]

    # 提示词模版
    prompt = PromptTemplate(
        template=load_prompt("extend_keywords_for_value_recall"),
        input_variables=["query"]
    )

    # 输出解析器
    output_parser = JsonOutputParser()

    # 构建langchain链
    chain = prompt | llm | output_parser

    # 执行链获取结果
    result = await chain.ainvoke({"query": query})
    logger.info(f'recall_value llm keywords: {result}')

    # 合并关键字
    keywords = list(set(keywords + result))
    logger.info(f'recall_value 合并关键字: {keywords}')

    # 保存所有召回指标信息的字典(去重)
    # {value_id: ValueInfoEs}
    recall_values_dict: dict[str, ValueInfoEs] = {}

    # 遍历keywords列表，对每个关键字进行召回
    for keyword in keywords:
        # 查询ES库,得到字段取值列表
        values: list[ValueInfoEs] = await value_es_repo.search(keyword)

        # 遍历去重保存
        for value in values:
            value_id = value["id"]
            if value_id not in recall_values_dict:
                recall_values_dict[value_id] = value

    # 将字典转为列表
    recall_values: list[ValueInfoEs] = list(recall_values_dict.values())

    logger.info(f"召回字段取值: {recall_values}")
    # logger.info(f"召回字段取值: {list(recall_values_dict.keys())}")

    return {"recall_values": recall_values}
