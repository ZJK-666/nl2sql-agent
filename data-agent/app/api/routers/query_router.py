from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

# 创建查询的路由器
query_router = APIRouter()

# 注册查询的路由
@query_router.post('/api/query')
async def query(q_schema: QuerySchema, q_service: QueryService = Depends(get_query_service)):
    return StreamingResponse(
        q_service.search(q_schema.query),
        media_type='text/event-stream'
    )

