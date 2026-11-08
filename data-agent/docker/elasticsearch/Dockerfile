# 基于Elasticsearch 8.19.10版本构建镜像
FROM elasticsearch:8.19.10

# 切换到root用户，以执行需要更高权限的操作
USER root

# 将IK分词器插件复制到临时目录/tmp
COPY plugins/elasticsearch-analysis-ik-8.19.10.zip /tmp/

# 安装IK分词器插件，--batch参数表示以非交互模式安装
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch \
    file:///tmp/elasticsearch-analysis-ik-8.19.10.zip

# 修改插件目录的所有者，确保elasticsearch用户有权限访问
RUN chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/plugins

# 切换回elasticsearch用户，以安全的方式启动服务
USER elasticsearch
