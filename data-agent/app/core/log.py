"""
封装日志模块：
    1.定制日志输出格式，控制输出级别
    2.自动将日志文件保存到日志文件
    3.指定日志文件的大小，超过会自动创建一个新文件
    4.指定日志文件的有效期，过期会自动删除文件
    5.记录当前日志输出的是哪个请求的id
"""
import sys
import uuid
from pathlib import Path

from loguru import logger

from app.conf.app_config import app_config
from app.core.context import get_req_id

# 配置日志格式
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 绿色显示 日志时间（精确到毫秒）
    "<level>{level: <8}</level> | "  # 按级别颜色显示 日志级别（左对齐，占8个字符）
    "<magenta>request_id - {extra[request_id]}</magenta> | "  # 品红色显示 request_id（从日志extra中获取）
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 青色显示 日志所在文件、函数、行号
    "<level>{message}</level>"  # 按级别颜色显示 日志正文
)

# 该函数由loguru在每次输出日志前调用
def inject_request_id(record):
    # 获取请求id
    request_id = get_req_id()
    if not request_id:
        # 如果请求id为0，则生成一个随机id
        request_id = uuid.uuid4()
    # 将 request_id 存入日志记录的 extra 字段，供日志格式中 {extra[request_id]} 调用
    record["extra"]["request_id"] = request_id


# 移除日志默认的配置
logger.remove()

# 给日志打补丁，使其在输出每条日志前执行inject_request_id函数，注入request_id
logger = logger.patch(inject_request_id)

# 如果配置中开启了控制台日志输出
if app_config.logging.console.enable:
    # 添加控制台日志输出器
    logger.add(sink=sys.stdout, level=app_config.logging.console.level, format=log_format)

# 日志文件保存路径
path = Path(__file__).parents[2] / "logs/app.log"

# 如果配置中开启了文件日志输出
if app_config.logging.file.enable:
    # 添加文件日志输出器
    logger.add(
        sink=path,  # 日志文件保存路径
        level=app_config.logging.file.level,  # 文件日志输出级别
        format=log_format,  # 使用自定义的日志格式
        rotation=app_config.logging.file.rotation,  # 日志文件分割规则（如按大小/时间）
        retention=app_config.logging.file.retention,  # 日志文件保留时长
        encoding="utf-8"  # 日志文件编码格式
    )


if __name__ == '__main__':
    # 日志级别，严重程度，由低到高
    logger.debug("这是一条 debug 日志")
    logger.info("这是一条 info 日志")
    logger.warning("这是一条 warning 日志")
    logger.error("这是一条 error 日志")
    logger.critical("这是一条 critical 日志")


    name = "Tony"
    age = 20
    # 可以运行
    logger.info(f"用户 {name} 的年龄是 {age}")
    # 但 Loguru 推荐：
    logger.info("用户 {} 的年龄是 {}", name, age)

    # 这些日志输出有默认的配置
    # 要自定义配置，需先移除默认配置


