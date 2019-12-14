# 基础镜像信息
FROM tiangolo/meinheld-gunicorn:python3.6
# 创建目录
RUN mkdir -p /usr/local/fundhelper
# 拷贝文件
ADD ./ /usr/local/fundhelper
# 设置工作目录
WORKDIR /usr/local/fundhelper
# 安装requirements
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "./main.py"]
EXPOSE 5000
