from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

# 初始化对话模型
llm = init_chat_model(
    model=app_config.llm.model_name,
    api_key=app_config.llm.api_key,
    # api_key=os.getenv('环境变量'),
    # model_provider='openai',
    # base_url='...',
    temperature=0
)

# model_provider='openai'
# 指定模型提供商
# 我们使用的 Qwen和DeepSeek
# 都是遵循openai协议的模型
# 可以不写模型提供商

# base_url='...',
# 指定模型服务地址
# DeepSeek模型不需要设置
# langchain内部可以识别
# 如果使用千问模型需要设置

# temperature=0
# 采样温度，取值范围通常是 0~2
# 设为 0 表示确定性输出
# 每次都倾向选概率最高的 token
# 结果稳定可复现，适合 SQL 生成等
# 对准确性要求高的任务
# (不像写文案需要更高的创造性)
# 值越大输出越随机、越有创造性

# 测试
if __name__ == '__main__':
    for chunk in llm.stream("你是什么模型？"):
        print(chunk.text, end="", flush=True)

# llm.stream() 调用流式接口
# 参数 "你是什么模型？"
# 是发送给模型的用户输入消息
# 返回一个生成器（generator）
# 模型每生成一小段文本（chunk）
# 就 yield 产出结果，
# 而不是等全部生成完才一次性返回
# for chunk in ...：遍历生成器
# 每次拿到一个文本片段 chunk
# LangChain的AIMessageChunk对象
# chunk.text：从该 chunk
# 中取出纯文本内容（字符串）
# print(...,end="",flush=True)
# end = "" 打印后不换行（默认\n）
# 这样多个 chunk 能连成一句话
# flush=True 立即刷新缓冲区输出到终端
# 流式输出时如果不flush，输出可能被缓冲
# 等到程序结束才一次性显示
# 就失去了“边生成边显示”的效果