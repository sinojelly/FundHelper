# 基础镜像信息
FROM tiangolo/meinheld-gunicorn:python3.6

# 安装node,保证环境中有JS环境
RUN wget https://nodejs.org/dist/v10.15.3/node-v10.15.3-linux-x64.tar.xz 
RUN xz -d node-v10.15.3-linux-x64.tar.xz
RUN tar -xvf node-v10.15.3-linux-x64.tar

# 添加软链接
RUN ln -s /app/node-v10.15.3-linux-x64/bin/node /usr/local/bin/node 
RUN ln -s /app/node-v10.15.3-linux-x64/bin/npm /usr/local/bin/npm
# node -v  可验证node是否安装成功

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
