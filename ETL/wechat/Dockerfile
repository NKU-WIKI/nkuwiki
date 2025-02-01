# 使用多阶段构建减少镜像大小
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

# 确保PATH包含用户安装目录
ENV PATH=/root/.local/bin:$PATH

# 使用非root用户
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "import_wechat.py", "/app/data", "--resume"]