from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class DWMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 获取当前表所有字段的类型
    async def get_column_types(self, table_name: str)->dict:
        # 在dw数据库右键新建查询控制台，执行下列sql语句
        # "show columns from dim_customer"
        # 查询结果中有两个字段：Field（字段名）和 Type（字段类型）

        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {row.Field:row.Type for row in result.all()}

    # 获取当前表指定字段的前N个值
    async def get_column_values(self, table_name: str, column_name: str, limit: int = 5)->list:
        # 在dw数据库右键新建查询控制台，执行下列sql语句
        # "select distinct gender from dim_customer limit 10"
        # 查询结果中有一个字段名和所有值（去重）

        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().all()

    # 获取数据库信息
    async def get_db_info(self)->dict:
        # 查询数据库版本
        result = await self.session.execute(text("select version()"))
        # 解析结果
        version = result.scalar()

        # 查询数据方言
        dialect = self.session.get_bind().dialect.name

        return {"version": version, "dialect": dialect}

    # 校验SQL
    async def to_validate_sql(self, sql: str):
        await self.session.execute(text(f"explain {sql}"))
        # 如果抛出异常，说明SQL不合法

    # 执行SQL
    async def to_execute_sql(self, sql: str)->list[dict]:
        result = await self.session.execute(text(sql))
        # rowMapping对象，不能序列化（不能转为JSON）
        # return result.mappings().all()
        return [dict(row) for row in result.mappings().all()]
