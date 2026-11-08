import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


# 节点：过滤指标信息
async def filter_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 输出给前端的数据（前后端约定好的数据格式）
    runtime.stream_writer({"stage":"过滤指标信息"})

    query = state["query"]
    metric_infos = state["metric_infos"]

    # 利用大模型对metric_infos进行过滤
    # 最终生成列表：[指标1，指标2]

    try:
        # 提示词模版
        prompt = PromptTemplate(
            template=load_prompt("filter_metric_info"),
            input_variables=["query", "metric_infos"]
        )

        # 输出解析器
        output_parser = JsonOutputParser()

        # 构建langchain链
        chain = prompt | llm | output_parser

        # 执行链获取结果
        result = await chain.ainvoke({"query": query, "metric_infos": yaml.dump(
            metric_infos, allow_unicode=True, sort_keys=False
        )})

        logger.info(f'filter_metric llm: {result}')

        # 过滤metric_infos中的指标
        for metric in metric_infos[:]:
            if metric["name"] not in result:
                metric_infos.remove(metric)

        logger.info(f'过滤指标信息完成:{metric_infos}')
        return {"metric_infos": metric_infos}

    except Exception as e:
        logger.error(f'过滤指标信息失败:{str(e)}')
        raise # 抛出所有的错误，方便调试
        # raise e # 抛出当前的错误，方便调试
