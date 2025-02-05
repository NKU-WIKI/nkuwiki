FROM python:3.12-slim-bookworm

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 复制环境变量文件
COPY .env .

CMD ["python", "import_wechat.py", "/data/wechat", "--resume"]