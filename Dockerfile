FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 优化pip
RUN pip install --no-cache-dir --upgrade pip

# 复制依赖文件并安装
# 这样做可以利用Docker的层缓存机制，只有当requirements.txt改变时，才会重新安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有应用代码
COPY . .

# 暴露应用端口
EXPOSE 8000

# 启动应用的命令
CMD ["python", "app.py", "--api", "--port", "8000"] 