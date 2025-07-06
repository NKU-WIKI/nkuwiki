FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 优化pip
# 默认情况下，pip会使用自身的缓存，除非您明确指定 --no-cache-dir

# 设置主要的pip镜像源（例如清华源）
# global.index-url 只能配置一个主源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Step 1: Install base dependencies from the main requirements file
COPY requirements.txt .
# 在此步中，pip将尝试使用自身的缓存（如果存在），同时也会利用Docker的层缓存。
# 另外，除了主源（清华源），再添加一个额外的源（阿里云），以备某些包在主源找不到时可以从额外源获取。
RUN pip install -r requirements.txt \
    --no-cache-dir \
    --default-timeout=100 \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com


# Step 2: Install the correct torch version from the local wheel file
# Copy the local wheel file into the image
COPY static/wheels/torch-2.3.0+cpu-cp312-cp312-linux_x86_64.whl /tmp/
# Install from the local file and remove it in the same layer
RUN pip install /tmp/torch-2.3.0+cpu-cp312-cp312-linux_x86_64.whl --no-cache-dir && \
    rm /tmp/torch-2.3.0+cpu-cp312-cp312-linux_x86_64.whl

# Step 3: Install torch-dependent packages
COPY requirements-torch.txt .
# 同样，对于这些依赖，如果它们依赖于torch的特定构建，可能也需要PyTorch的官方源。
# 同时保留阿里云作为备用。pip会尝试缓存这些包。
RUN pip install -r requirements-torch.txt \
    --no-cache-dir \
    --default-timeout=100 \
    --extra-index-url https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

# 复制所有应用代码
COPY . .

# 暴露应用端口
EXPOSE 8000

# 启动应用的命令
CMD ["python", "app.py", "--api", "--port", "8000"]
