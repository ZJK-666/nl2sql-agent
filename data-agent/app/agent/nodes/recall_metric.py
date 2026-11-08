from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.prompt.prompt_loader import load_prompt


# 节点：召回指标信息
async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 输出给前端的数据（前后端约定好的数据格式）
    runtime.stream_writer({"stage":"召回指标信息"})

    query = state["query"]
    keywords = state["keywords"]
    embedding_client = runtime.context["embedding_client"]
    metric_qdrant_repo = runtime.context["metric_qdrant_repo"]

    # 1.用大模型对query进行语义分词，并与jieba分词结果合并
    # 2.拿合并后的分词去做召回（关键字向量化）
    # 3.拿向量去查询qdrant向量库
    # 4.得到字段信息列表 list[MetricInfoQdrant]
    # 5.返回 list[MetricInfoQdrant]

    # 提示词模版
    prompt = PromptTemplate(
        template=load_prompt("extend_keywords_for_metric_recall"),
        input_variables=["query"]
    )

    # 输出解析器
    output_parser = JsonOutputParser()

    # 构建langchain链
    chain = prompt | llm | output_parser

    # 执行链获取结果
    result = await chain.ainvoke({"query": query})
    logger.info(f'recall_metric llm keywords: {result}')

    # 合并关键字
    keywords = list(set(keywords + result))
    logger.info(f'recall_metric 合并关键字: {keywords}')

    # 保存所有召回指标信息的字典(去重)
    # {metric_id: MetricInfoQdrant}
    recall_metrics_dict: dict[str, MetricInfoQdrant] = {}

    # 遍历keywords列表，对每个关键字进行召回
    for keyword in keywords:
        # 将keyword向量化
        vector = await embedding_client.aembed_query(keyword)
        # 查询向量库,得到字段信息列表
        payloads: list[MetricInfoQdrant] = await metric_qdrant_repo.search(vector)

        # 遍历去重保存
        for payload in payloads:
            metric_id = payload["id"]
            if metric_id not in recall_metrics_dict:
                recall_metrics_dict[metric_id] = payload

    # 将字典转为列表
    recall_metrics: list[MetricInfoQdrant] = list(recall_metrics_dict.values())

    logger.info(f"召回指标信息: {recall_metrics}")

    return {"recall_metrics": recall_metrics}
