import asyncio

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.conf.meta_config import meta_config
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw_mysql_repository import DWMysqlRepository
from app.repositories.mysql.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


async def start_build():
    logger.info("构建元数据知识库 开始")

    # 初始化所有客户端管理器
    embedding_client_manager.init()
    es_client_manager.init()
    qdrant_client_manager.init()
    dw_mysql_client_manager.init()
    meta_mysql_client_manager.init()

    # 调用 meta_knowledge_service.py
    # 中的build()方法来构建元数据知识库
    # 构建元数据知识库，成功则提交事务，失败则回滚事务
    try:
        async with (dw_mysql_client_manager.session_factory() as dw_session,
                    meta_mysql_client_manager.session_factory() as meta_session):
            # 创建service对象
            service = MetaKnowledgeService(
                dw_mysql_repo=DWMysqlRepository(dw_session),
                meta_mysql_repo=MetaMysqlRepository(meta_session),
                value_es_repo=ValueEsRepository(es_client_manager.client),
                column_qdrant_repo=ColumnQdrantRepository(qdrant_client_manager.client),
                metric_qdrant_repo=MetricQdrantRepository(qdrant_client_manager.client),
                embedding_client=embedding_client_manager.client
            )

            # 调用build()方法
            await service.build(meta_config)
            # 成功，提交事务
            await dw_session.commit()
            await meta_session.commit()

        logger.info("构建元数据知识库 完成")
    except Exception as e:
        # 失败，回滚事务
        await dw_session.rollback()
        await meta_session.rollback()
        logger.error(f"构建元数据知识库 失败：{str(e)}")
        raise e # 方便调试
    finally:
        # 关闭所有客户端
        await es_client_manager.close()
        await qdrant_client_manager.close()
        await dw_mysql_client_manager.close()
        await meta_mysql_client_manager.close()
        # embedding_client 不需要关闭

if __name__ == '__main__':
    asyncio.run(start_build())
