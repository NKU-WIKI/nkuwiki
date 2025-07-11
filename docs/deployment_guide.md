# nkuwiki 部署指南

本文档提供 `nkuwiki` 项目的标准化部署流程，推荐使用 `Docker` 和 `docker-compose` 来管理后端依赖服务，以确保环境的一致性和简化部署过程。

## 1. 先决条件

在开始之前，请确保你的系统已经安装了以下软件：

- **Git**: 用于克隆项目代码。
- **Python 3.10+**: 项目运行环境。
- **Docker**: 用于运行容器化服务。
- **Docker Compose**: 用于编排多容器应用。（通常随 Docker Desktop 一起安装）。

如果你的系统中没有安装 Docker 和 Docker Compose，请参考官方文档进行安装：
- [安装 Docker Engine](https://docs.docker.com/engine/install/)
- [安装 Docker Compose](https://docs.docker.com/compose/install/)

## 2. 获取项目代码

详细步骤请参考 `README.md` 中的 [环境准备](#-快速开始) 部分。核心命令如下：

```bash
git clone https://github.com/NKU-WIKI/nkuwiki.git
cd nkuwiki
git submodule update --init --recursive
```

## 3. 使用 Docker Compose 启动后端服务

项目根目录下的 `docker-compose.yml` 文件已经预先配置好了所有必需的后端服务，包括 `MySQL`, `Qdrant`, 和 `Redis`。

**启动所有服务:**

在项目根目录下，执行以下命令：

```bash
docker-compose up -d
```
`-d` 参数会使容器在后台运行。

**验证服务状态:**

你可以使用以下命令检查所有容器是否正在正常运行：

```bash
docker-compose ps
```
你应该能看到 `mysql`, `qdrant`, `redis` 等服务的状态为 `Up` 或 `Running`。

## 4. 配置项目

`docker-compose` 启动的服务使用的是默认的配置。你需要更新本地的 `config.json` 文件，使其能够连接到这些由Docker启动的服务。

在你的 `config.json` 文件中，确保数据库相关的配置如下：

```json
{
  "etl": {
    "data": {
      "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "your_mysql_root_password", // 替换为docker-compose.yml中设置的密码
        "database": "nkuwiki",
        "charset": "utf8mb4"
      },
      "qdrant": {
        "host": "127.0.0.1",
        "port": 6333
      },
      "redis": {
          "host": "127.0.0.1",
          "port": 6379,
          "password": "",
          "db": 0
      }
    }
  }
}
```
**注意**:
- `host` 应为 `127.0.0.1` 或 `localhost`，因为你是从主机连接到Docker容器暴露的端口。
- `password` 必须与 `docker-compose.yml` 文件中为MySQL设置的 `MYSQL_ROOT_PASSWORD` 环境变量的值完全一致。

## 5. 运行应用

当所有后端服务通过 Docker 正常运行，并且 `config.json` 配置正确后，你就可以像在 `README.md` 中描述的那样启动应用了。

**启动API服务:**
```bash
python app.py --api --port 8000
```

**运行ETL流程:**
```bash
python etl/daily_pipeline.py
```

## 6. 管理服务

- **停止服务**: `docker-compose stop`
- **停止并删除容器**: `docker-compose down`
- **查看日志**: `docker-compose logs -f <service_name>` (例如: `docker-compose logs -f mysql`)

通过遵循本指南，你可以快速、可靠地部署和运行 `nkuwiki` 项目。

## 运行项目

### 基本运行

```bash
# 启动智能问答服务
cd nkuwiki & python3 app.py

# 启动爬虫任务 (示例)
# 确保已安装 playwright install chromium
cd nkuwiki & python3 ./etl/crawler/wechat.py
```

## 数据库服务部署

### Docker部署

#### 安装Docker

##### Linux系统（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# 添加当前用户到docker组（免sudo运行docker）
sudo usermod -aG docker $USER

# 重新登录以使权限生效
```

##### CentOS/RHEL系统

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker

# 添加当前用户到docker组（免sudo运行docker）
sudo usermod -aG docker $USER

# 重新登录以使权限生效
```

##### Windows系统

1. 下载Docker Desktop安装程序：https://www.docker.com/products/docker-desktop/
2. 运行安装程序，按照提示完成安装
3. 安装完成后启动Docker Desktop

##### macOS系统

1. 下载Docker Desktop安装程序：https://www.docker.com/products/docker-desktop/
2. 将下载的.dmg文件拖到Applications文件夹
3. 启动Docker Desktop

#### 部署MySQL和Qdrant

##### MySQL

```bash
docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=your_password -v path\to\your\data\mysql:/var/lib/mysql mysql:latest

# 示例
# docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=123456 -v d:\code\nkuwiki\etl\data\mysql:/var/lib/mysql mysql:latest
```

##### Qdrant

```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
    -v path\to\your\data\qdrant:/qdrant/storage \
    qdrant/qdrant:latest

# 示例
# docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v d:\code\nkuwiki\etl\data\qdrant:/qdrant/storage qdrant/qdrant:latest
```

### 源代码部署

#### MySQL

##### Linux系统（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql

# 设置root密码
sudo mysql_secure_installation
```

##### CentOS/RHEL系统

```bash
sudo yum install mysql-server
sudo systemctl enable mysqld
sudo systemctl start mysqld

# 获取临时root密码
sudo grep 'temporary password' /var/log/mysqld.log

# 设置新密码
mysql -uroot -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';
```

##### Windows系统

1. 下载MySQL安装程序：https://dev.mysql.com/downloads/installer/
2. 运行安装程序，按照提示完成安装
3. 安装过程中会提示设置root密码

##### macOS系统

```bash
brew install mysql
brew services start mysql

# 设置root密码
mysql_secure_installation
```

#### Qdrant

##### Linux系统（Ubuntu/Debian/CentOS/RHEL）

```bash
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz -o qdrant.tar.gz
tar -xvf qdrant.tar.gz
cd qdrant

# 启动qdrant服务
./qdrant
```