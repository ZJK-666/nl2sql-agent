import asyncio

from sqlalchemy import text, Select
from app.conf.app_config import DBConfig, app_config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker

from app.models.mysql.table_info_mysql import TableInfoMySQL


# 操作mysql数据库的客户端管理器类
class MySQLClientManager:
    # 初始化实例属性
    def __init__(self, config: DBConfig):
        self.config = config
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker | None = None

    # 获取连接的url
    def _get_url(self):
        # "mysql+asyncmy://user:pass@hostname/dbname?charset=utf8mb4"
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    # 初始化客户端
    def init(self):
        # 创建引擎
        self.engine = create_async_engine(
            self._get_url(),
            pool_size=10, # 初始创建的常驻连接数，用完了归还连接池，如果超过了会创建临时连接，用完后关闭
            max_overflow=10, # 临时连接数，超过这个数会报错
            pool_pre_ping=True # 每次从连接池中获取连接时，会执行一个ping命令，如果连接不可用，会从连接池中移除并自动创建一个新的连接
        )

        # 创建会话工厂
        self.session_factory = async_sessionmaker(
            self.engine,
            autobegin=True,  # 自动开启事务，并不会自动关闭事务
            expire_on_commit=False,  # 事务提交后，还可以读取ORM对象中的属性
            autoflush=True  # 自动刷新，自动将未提交事务的数据同步到数据库的暂存区，可以查询到最新的数据
        )

    # 关闭管理器，释放资源
    async def close(self):
        await self.engine.dispose()

# 创建操作dw数据库的客户端管理器
dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)

# 创建操作meta数据库的客户端管理器
meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)


if __name__ == '__main__':
    async def test():
        # 初始化客户端
        dw_mysql_client_manager.init()

        # 创建异步会话对象
        # session = AsyncSession(dw_mysql_client_manager.engine)
        # 执行sql语句
        # session.execute(sql)
        # 需要手动关闭会话

        # 创建异步会话对象
        # async with AsyncSession(
        #         dw_mysql_client_manager.engine,
        #         autobegin=True, # 自动开启事务，并不会自动关闭事务
        #         expire_on_commit=False, # 事务提交后，还可以读取ORM对象中的属性
        #         autoflush=True # 自动刷新，自动将未提交事务的数据同步到数据库的暂存区，可以查询到最新的数据
        # ) as session:

        async with dw_mysql_client_manager.session_factory() as session:
            # 执行sql语句
            # text("select * from dim_customer limit 2") 将sql字符串包装成一个可执行对象
            result = await session.execute(text("select * from dim_customer limit 2"))
            # print(result) # <sqlalchemy.engine.cursor.CursorResult object...>

            # rows = result.all() # 是一个row对象的列表
            # print(rows) # [('C001', '李伟', '男', '黄金'), ('C002', '王芳', '女', '白银')]
            # print(rows[0][1]) # 李伟

            # rows = result.mappings().all() # 是一个RowMapping对象的列表
            # print(rows) # [{'customer_id': 'C001', 'customer_name': '李伟', 'gender': '男', 'member_level': '黄金'}, {'customer_id': 'C002', 'customer_name': '王芳', 'gender': '女', 'member_level': '白银'}]

            rows = result.scalars().all() # 包含每条数据第一个值的列表
            print(rows) # ['C001', 'C002']

        # 关闭管理器
        await dw_mysql_client_manager.close()
    # 执行协程
    # asyncio.run(test())

    async def test_orm():
        # 初始化客户端
        meta_mysql_client_manager.init()

        # 创建异步会话对象
        async with meta_mysql_client_manager.session_factory() as session:
            # 创建ORM对象
            table_info1 = TableInfoMySQL(
                id='test_tabel1',
                name='test_tabel1',
                role='fact',
                description='测试用的表格，用于测试ORM操作111'
            )
            table_info2 = TableInfoMySQL(
                id='test_tabel2',
                name='test_tabel2',
                role='fact',
                description='测试用的表格，用于测试ORM操作222'
            )

            # 增加数据（将ORM对象添加到会话中）
            session.add(table_info1)
            session.add(table_info2)

            # 修改fact_order表中的数据
            # table_info2 = await session.get(TableInfoMySQL,'fact_order')
            # table_info2.description = '订单事实表，记录订单数量和金额等核心指标。123'

            # 查询一条数据
            # result = await session.get(TableInfoMySQL, 'dim_date')
            # print(result) # <TableInfoMySQL object ...>
            # print(result.name) # dim_date
            # print(result.description) # 时间维度表，用于多时间粒度分析。

            # 查询多条数据
            # result = await session.execute(Select(TableInfoMySQL).limit(2))
            # table_infos: list[TableInfoMySQL] = result.scalars().all() # Sequence序列
            # print(table_infos) # [TableInfoMySQL object,TableInfoMySQL object]
            # print(table_infos[0].name) # dim_customer
            # print(table_infos[1].name) # dim_date
            # for table_info in table_infos:
            #     print(table_info.name) # dim_customer dim_date

            # 提交事务，数据才会存到数据库，否则在数据库暂存区
            await session.commit()

            # 提交事务后再访问ORM对象属性
            # expire_on_commit = False, # 事务提交后，还可以读取ORM对象中的属性
            # expire_on_commit = True, # 事务提交后，不可以读取ORM对象中的属性
            print(table_info1.name) # test_tabel

            # 删除数据
            await session.delete(table_info1)

            print(table_info1.name)  # 提问删除操作后是否能访问？能

            # 提交事务，数据才会存到数据库，否则在数据库暂存区
            await session.commit()

        # 关闭管理器
        await meta_mysql_client_manager.close()
    # 执行协程
    asyncio.run(test_orm())
