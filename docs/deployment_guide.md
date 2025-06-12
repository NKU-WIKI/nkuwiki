# nkuwiki 部署指南

本文档提供了nkuwiki项目的部署说明，包括运行项目、部署MySQL和Qdrant服务等内容。

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

##### Windows系统

1. 下载Qdrant：https://github.com/qdrant/qdrant/releases
2. 解压下载的文件
3. 运行qdrant.exe

##### macOS系统

```bash
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-apple-darwin.tar.gz -o qdrant.tar.gz
tar -xvf qdrant.tar.gz
cd qdrant

# 启动qdrant服务
./qdrant
```

#### 配置MySQL服务

```bash
# mysql配置（根据需要修改）
# linux/macos
sudo mysql
CREATE USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON *.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

## 开发指南

### 添加新爬虫

1. 在`etl/crawler`目录创建新的爬虫类，继承`BaseCrawler`
2. 添加`self.platform`, `self.base_url`, `self.content_type`等配置
3. 实现`login_for_cookies`方法（如果需要登录）, `scrape`和`download`方法

### 添加新服务通道

1. 在`services`目录创建新的通道类
2. 在`services/channel_factory.py`中注册新通道

### 添加新AI智能体

1. 在`core/agent/`目录下添加新的AI提供商目录
2. 实现继承自`Agent`类的自定义智能体
3. 在`agent_factory.py`中注册您的智能体

### 调试

- 建议使用`services/terminal`模块进行命令行调试，配置`channel_type = terminal`
- 查看`logs/`目录下的日志文件排查问题

更详细的开发文档请参考[docs](../docs)目录。 