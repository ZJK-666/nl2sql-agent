from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


# 节点：校验SQL
async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 输出给前端的数据（前后端约定好的数据格式）
    runtime.stream_writer({"stage":"校验SQL"})

    sql = state["sql"]
    dw_mysql_repo = runtime.context["dw_mysql_repo"]

    try:
        # 校验SQL语句是否合法
        await dw_mysql_repo.to_validate_sql(sql)

        logger.info(f'校验SQL成功:{sql}')

        # 没有异常返回 None
        return {"error": None}

    except Exception as e:
        logger.error(f'校验SQL失败:{str(e)}')
        # 有异常返回 异常信息
        return {"error": f"SQL语法错误:{str(e)}"}
