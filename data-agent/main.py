# 导入FastAPI核心类
import uuid

from fastapi import FastAPI, Request

from app.api.routers.query_router import query_router
from app.core.context import set_req_id
from app.core.lifespan import lifespan

# 创建FastAPI应用实例，并注册生命周期组件
app = FastAPI(lifespan=lifespan)

# 绑定查询router
app.include_router(query_router)


# 中间件：为每个请求创建一个唯一id
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    # 调用路径函数之前进行业务处理
    set_req_id(uuid.uuid4())
    # 调用路径函数
    response = await call_next(request)
    # 调用路径函数之后进行业务处理
    return response
