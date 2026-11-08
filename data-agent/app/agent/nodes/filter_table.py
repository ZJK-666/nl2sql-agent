import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


# 节点：过滤表信息
async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 输出给前端的数据（前后端约定好的数据格式）
    runtime.stream_writer({"stage":"过滤表信息"})

    query = state["query"]
    table_infos = state["table_infos"]

    # 利用大模型对table_infos进行过滤
    # 最终生成字典：{表名1：[字段1，字段2]，表名2：[字段1，字段2]}

    try:
        # 提示词模版
        prompt = PromptTemplate(
            template=load_prompt("filter_table_info"),
            input_variables=["query", "table_infos"]
        )

        # 输出解析器
        output_parser = JsonOutputParser()

        # 构建langchain链
        chain = prompt | llm | output_parser

        # 执行链获取结果
        # table_infos字典格式，传给大模型就是JSON字符串
        # 大模型也能处理，就是数据量更大，比较消耗token
        # result = await chain.ainvoke({"query": query, "table_infos": table_infos})
        result = await chain.ainvoke({"query": query, "table_infos": yaml.dump(
            table_infos, allow_unicode=True, sort_keys=False
        )})
        # yaml是Python操作yaml的核心库
        # dump()方法的作用是：将Python对象（字典、列表等）转换成yaml格式字符串/文件
        # allow_unicode=True 保留中文，不转换为Unicode编码
        # sort_keys=False 不对键进行排序，保留原始数据顺序

        logger.info(f'filter_table llm: {result}')

        # 遍历浅拷贝出来的table_infos
        for table_info in table_infos[:]:
            # 将不在result中的表名从table_infos中删除
            if table_info["name"] not in result:
                table_infos.remove(table_info) # 删除表
            else:
                # 当前表名在result中，过滤表名对应的字段
                columns = table_info["columns"]
                for column in columns[:]:
                    if column["name"] not in result[table_info["name"]]:
                        columns.remove(column) # 删除字段

        logger.info(f'过滤表信息完成:{table_infos}')
        return {"table_infos": table_infos}

    except Exception as e:
        logger.error(f'过滤表信息失败:{str(e)}')
        raise # 抛出所有的错误，方便调试
        # raise e # 抛出当前的错误，方便调试
