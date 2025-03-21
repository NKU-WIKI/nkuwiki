# nkuwiki 安装指南

本文档提供了nkuwiki项目的安装步骤，包括环境准备、获取代码和安装依赖。

## 环境准备

- python 3.10.12
- python3-venv(linux可能需要单独安装，windows/macos一般内置) or miniconda3
- git
- docker or docker-desktop (windows)(可选，用于容器化部署)
- mysql latest (可选，用于rag)
- qdrant latest (可选，用于rag)

## 获取代码

```bash
# 克隆仓库
git clone https://github.com/NKU-WIKI/nkuwiki.git

# 克隆微信小程序子模块
git submodule update --init --recursive
cd nkuwiki
```

## 安装依赖

### 方式一：使用 venv 创建虚拟环境

step1 安装venv模块

```bash
# 安装venv模块
pip install venv  # 如果需要安装
```

step2 创建虚拟环境

```bash
# 创建虚拟环境（默认在当前目录）
python3 -m venv nkuwiki --python=3.10.12

# 或者指定安装路径
# python3 -m venv path/to/yourvenv --python=3.10.12
# 例如 python3 -m venv /opt/venvs/nkuwiki --python=3.10.12 (linux)
# python3 -m venv d:\venvs\nkuwiki --python=3.10.12 (windows)
```

step3 激活虚拟环境

```bash
# 当前目录环境激活
# linux/macos
source nkuwiki/bin/activate

# windows
nkuwiki\scripts\activate

# 指定路径环境激活
# linux/macos
# source path/to/yourvenv/bin/activate
# 例如 source /opt/venvs/nkuwiki/bin/activate

# windows
# path\to\yourvenv\scripts\activate
# 例如 d:\venvs\nkuwiki\scripts\activate
```

### 方式二：使用 conda 创建虚拟环境

step1 安装miniconda3

```bash
# 下载miniconda安装程序
# windows: https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
# linux: https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# macos: https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# linux/macos安装
# bash miniconda3-latest-linux-x86_64.sh
# 按照提示完成安装并初始化
# conda init

# windows安装
# 运行下载的exe文件，按照提示完成安装
```

step2 创建虚拟环境

```bash
# 创建名为nkuwiki的环境，指定python版本为3.10.12
conda create -n nkuwiki python=3.10.12

# 或者指定安装路径
# conda create -p path/to/conda/envs/nkuwiki python=3.10.12
# 例如 conda create -p /opt/conda/envs/nkuwiki python=3.10.12 (linux/macos)
# conda create -p d:\conda\envs\nkuwiki python=3.10.12 (windows)
```

step3 激活虚拟环境

```bash
# 使用环境名激活
conda init
conda activate nkuwiki

# 或者使用路径激活
# conda activate path/to/conda/envs/nkuwiki
# 例如 conda activate /opt/conda/envs/nkuwiki (linux/macos)
# conda activate d:\conda\envs\nkuwiki (windows)
```

### 安装项目依赖

```bash
pip install -r requirements.txt
playwright install chromium # 使用playwright内置浏览器
```

> 注意：项目依赖包含多种AI模型接口，如 Claude API、Google Gemini、智谱AI等。确保您有足够的网络连接和磁盘空间来安装这些依赖。 