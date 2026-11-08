import asyncio
from contextvars import ContextVar

# 创建上下文变量对象，用于在异步/多请求场景下存储和获取当前请求的唯一标识req_id
# 参数1：上下文变量的名称，用于标识变量的用途
# 参数2：指定默认值，当未显式设置req_id时，获取到的值为''
_request_id_context_var: ContextVar = ContextVar("req_id", default='')

# 设置请求id
def set_req_id(rid: str):
    _request_id_context_var.set(rid)

# 获取请求id
def get_req_id()->int:
    return _request_id_context_var.get()

if __name__ == '__main__':
    # 模拟两个异步请求
    # 多个协程之间的数据互相隔离
    async def request1():
        print(f'请求1开始执行，req_id={get_req_id()}') # ''
        set_req_id('1')
        print(f'请求1执行结束，req_id={get_req_id()}') # '1'

    async def request2():
        print(f'请求2开始执行，req_id={get_req_id()}') # ''
        set_req_id('2')
        print(f'请求2执行结束，req_id={get_req_id()}') # '2'

    async def test():
        await asyncio.gather(request1(), request2())

    asyncio.run(test())