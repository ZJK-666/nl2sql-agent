import asyncio

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from app.conf.app_config import EmbeddingConfig, app_config

# 操作Embedding的客户端管理器类
class EmbeddingClientManager:
    # 初始化实例属性
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.client: HuggingFaceEndpointEmbeddings | None = None

    # 获取连接的url
    def _get_url(self):
        return f'http://{self.config.host}:{self.config.port}'

    # 初始化客户端
    def init(self):
        self.client = HuggingFaceEndpointEmbeddings(model=self._get_url())

    # embedding不需要关闭，使用后自动释放资源

# 创建embedding客户端管理器
embedding_client_manager = EmbeddingClientManager(app_config.embedding)

# 测试embedding操作
if __name__ == '__main__':
    async def test():
        # 初始化客户端
        embedding_client_manager.init()
        # 获取客户端
        embedding = embedding_client_manager.client

        # 对指定文本进行向量化
        text = 'hello world'
        result = embedding.embed_query(text)
        print(result) # [0.1, 0.2, 0.3,...]
        print(len(result)) # 1024维

    # 执行协程
    asyncio.run(test())