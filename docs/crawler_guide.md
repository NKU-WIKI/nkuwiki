# 爬虫模块开发指南

## 1. 模块定位与职责

`etl/crawler` 模块是 nkuwiki 项目ETL流程的**第一阶段（数据采集）**。其核心职责是从各类数据源（网站、微信公众号、校园集市等）抓取原始信息，并按照统一规范输出JSON文件到数据湖。

本指南聚焦于爬虫的开发实践。关于爬取的数据如何被后续流程（如索引、洞察生成）所使用，请参考统一的 **[ETL流程开发规范](./etl_pipeline_guide.md)**。

## 2. 核心概念与`BaseCrawler`基类

所有爬虫都继承自 `etl.crawler.base_crawler.BaseCrawler`，它封装了浏览器自动化（Playwright）、代理管理、Cookies管理、反检测脚本等通用功能。

### 关键初始化参数

- `platform` (str): 平台名称，如 `wechat`, `market`。这将决定数据存储的一级目录。
- `tag` (str): 任务标签，用于区分同一平台下的不同数据来源，如 `nkunews`, `nkuyouth`, `market_sell`。这将决定数据存储的二级目录。
- `headless` (bool): 是否以无头模式运行浏览器。服务器环境应设为 `True`。
- `use_proxy` (bool): 是否使用配置中的代理。

## 3. 爬虫开发流程

### 步骤一：创建爬虫类

在 `etl/crawler/` 目录下创建你的爬虫文件，并继承 `BaseCrawler`。

```python
# etl/crawler/my_crawler.py
from etl.crawler.base_crawler import BaseCrawler
from core.utils.logger import crawler_logger

class MyNewCrawler(BaseCrawler):
    def __init__(self, platform="my_platform", tag="default_tag", **kwargs):
        # 必须定义 platform 和 tag
        self.platform = platform
        self.tag = tag
        super().__init__(**kwargs)
        # 为日志绑定特定上下文
        self.logger = crawler_logger.bind(platform=self.platform, tag=self.tag)

    async def scrape(self, **kwargs):
        # 实现你的爬取逻辑
        pass
```

### 步骤二：实现 `scrape` 方法

`scrape` 方法是爬虫的核心，负责抓取元数据并调用下载方法。

```python
async def scrape(self, max_items=10):
    self.logger.info("开始爬取元数据...")
    await self.async_init()  # 初始化浏览器

    # 示例：爬取一个列表页
    # for i in range(max_items):
    #     item_data = {...} # 包含 title, url, publish_time 等
    #
    #     # 调用 download_item 保存单个文件
    #     await self.download_item(item_data)

    await self.close() # 关闭浏览器资源
    self.logger.info("元数据爬取与下载完成。")
```

### 步骤三：实现 `download_item` 方法

此方法负责处理单个数据单元的下载和保存，确保其符合下游规范。

```python
async def download_item(self, item_data: dict):
    """
    下载单个项目、处理并保存为标准JSON文件。
    item_data (dict): 从scrape方法传入的，至少包含url, title等信息的字典。
    """
    # 1. 访问详情页获取完整内容 (如果需要)
    # await self.page.goto(item_data['url'])
    # full_content = await self.page.text_content(...)

    # 2. 构建符合ETL规范的JSON数据
    final_data = {
        "id": self.generate_doc_id(item_data['url']),
        "title": item_data['title'],
        "content": "获取到的完整内容...",
        "url": item_data['url'],
        "platform": self.platform,
        "tag": self.tag,
        "publish_time": "ISO 8601格式的时间字符串"
    }

    # 3. 生成文件名和路径
    # self.get_save_path() 会自动处理年月目录
    save_path = self.get_save_path(
        doc_id=final_data['id'],
        publish_time_str=final_data['publish_time']
    )

    # 4. 保存文件
    await self.safe_write_json(save_path, final_data)
    self.logger.info(f"成功保存文件: {save_path}")

```

## 4. 数据输出规范

- **文件格式**: 标准JSON。
- **核心字段**: `id`, `title`, `content`, `url`, `platform`, `tag`, `publish_time`。
- **存储路径**: 必须遵循 `data/raw/{platform}/{tag}/{year}{month}/{article_id}.json` 结构。
    - `BaseCrawler` 中的 `get_save_path` 方法已经封装了此逻辑，请务必使用它来生成最终保存路径。

## 5. 运行与调试

- **直接运行**:
  ```bash
  python -m etl.crawler.your_crawler
  ```
- **调试技巧**:
  - 设置 `headless=False` 以观察浏览器操作。
  - 使用 `self.logger.debug()` 在关键步骤打印信息。
  - 善用 `await self.page.pause()`（在非无头模式下）来暂停执行并检查浏览器状态。
- **注意事项**:
  - **资源管理**: 确保任务结束时调用 `await self.close()`。
  - **异步编程**: 所有 `playwright` 操作和 `asyncio.sleep` 都必须 `await`。
  - **配置安全**: 敏感信息（如token）应放在 `config.json` 中，并确保该文件不被提交到代码库。

## 模块结构

```
etl/crawler/
├── __init__.py             # 模块初始化，配置加载
├── base_crawler.py         # 爬虫基类，封装通用逻辑
├── webpage_spider/         # 通用网页爬虫工具
├── xhs_spider/             # 小红书爬虫
├── douyin_spider/          # 抖音爬虫
├── wechat.py               # 微信公众号爬虫
├── market.py               # 校园集市爬虫
├── sina_finance.py         # 新浪财经爬虫
├── module_example.py       # 爬虫开发示例
├── init_script.js          # Playwright 浏览器初始化脚本，用于反检测
└── README.md               # 模块内部的开发指南
```

## 环境配置

1.  **Python 环境**: 确保已安装项目所需的 Python 版本及相关依赖（参考项目根目录的 `requirements.txt`）。
2.  **Playwright**: 首次运行或在新的环境中，可能需要安装 Playwright 及其浏览器驱动：
    ```bash
    playwright install
    # 或者仅安装 chromium
    playwright install chromium
    ```
3.  **配置文件**: 爬虫模块的特定配置项位于项目根目录的 `config.json` 文件中，主要集中在 `etl.crawler` 键下。关键配置包括：
    *   `proxy_pool`: 代理服务器地址，例如 `"http://127.0.0.1:7897"`。如果不需要代理，可以留空或确保 `use_proxy` 参数为 `false`。
    *   `market_token`: 访问校园集市 API 可能需要的 token。
    *   `accounts`: 各类平台账号配置，例如微信公众号列表 (`unofficial_accounts`, `university_official_accounts` 等)。

## 核心概念

### `BaseCrawler` 基类

所有具体的爬虫都继承自 `etl.crawler.base_crawler.BaseCrawler`。该基类提供了以下核心功能：

*   **异步浏览器操作**: 使用 `playwright` 库进行异步的浏览器控制。
*   **请求头与 User-Agent**: 随机选择 User-Agent，模拟不同浏览器。
*   **代理管理**: 支持从配置中加载代理池，并进行轮换。
*   **Cookies 管理**: 自动读取、保存和初始化 Cookies，支持设置 Cookies 有效期。
*   **反检测**: 注入 `init_script.js` 以尝试规避网站对自动化工具的检测。
*   **数据存储**: 爬取的数据默认保存在 `data/raw/<platform>/<tag>/` 目录下。
*   **日志记录**: 使用 `crawler_logger`记录爬虫运行过程中的信息。
*   **状态管理**: 通过锁文件 (`lock.txt`) 防止重复运行，通过计数器文件 (`counter.txt`) 记录统计信息。

### 爬虫实例初始化

初始化一个爬虫实例时，通常需要提供以下参数：

*   `debug` (bool): 是否开启调试模式。调试模式下通常日志更详细，反爬措施较少。默认为 `False`。
*   `headless` (bool): 是否以无头模式运行浏览器。无头模式不显示浏览器界面，适合服务器运行。默认为 `False`。
*   `use_proxy` (bool): 是否使用代理。默认为 `False`。
*   `tag` (str): 爬虫任务的标签，用于区分不同的爬取批次或目标，会影响数据存储路径。

特定爬虫可能还需要额外的参数，例如 `wechat.py` 中的 `authors`（指定要爬取的公众号列表）。

## 如何运行爬虫

大多数爬虫脚本可以直接作为 Python 文件运行，或者通过模块化方式执行。

**示例：运行微信公众号爬虫**

```python
# 假设在项目根目录下运行
# 方法一：直接运行脚本（如果脚本内有 main 执行逻辑）
# python etl/crawler/wechat.py

# 方法二：通过模块化方式运行（更推荐）
# python -m etl.crawler.wechat
```

**通用爬虫执行流程**

1.  **初始化爬虫对象**:
    ```python
    from etl.crawler.wechat import Wechat # 以微信爬虫为例

    # 实例化爬虫
    # Club Official Accounts
    wechat_crawler = Wechat(
        authors="club_official_accounts", # 对应 config.json 中的账号配置键名
        debug=False,
        headless=True, # 生产环境建议 True
        use_proxy=True # 根据需要配置
    )
    ```

2.  **执行爬取元数据**:
    调用爬虫对象的 `scrape()` 方法来抓取目标内容的元信息（如文章列表、标题、链接等）。
    ```python
    # 异步执行 scrape 方法
    import asyncio
    asyncio.run(wechat_crawler.scrape(max_article_num=5, total_max_article_num=100))
    # max_article_num: 单个公众号本次最多爬取的文章数
    # total_max_article_num: 本次任务总共最多爬取的文章数
    ```

3.  **执行下载内容**:
    调用爬虫对象的 `download()` 方法来下载元信息中链接对应的具体内容（如文章详情）。
    ```python
    # 异步执行 download 方法
    asyncio.run(wechat_crawler.download(debug=False, headless=True, use_proxy=True))
    ```
    注意：`download` 方法通常也需要 `debug`, `headless`, `use_proxy` 等参数，其行为与初始化时类似，但可以独立设置。

4.  **关闭爬虫**:
    显式调用 `close()` 方法释放资源，特别是浏览器和 Playwright 实例。
    ```python
    asyncio.run(wechat_crawler.close())
    ```

## 开发新爬虫

参考 `etl/crawler/README.md` 中的 "开发新爬虫" 部分，主要步骤如下：

1.  **继承 `BaseCrawler`**:
    ```python
    from etl.crawler import crawler_logger, config # 导入所需配置和日志
    from etl.crawler.base_crawler import BaseCrawler

    class MyNewCrawler(BaseCrawler):
        def __init__(self, platform_name="my_platform", tag="default_tag", **kwargs):
            self.platform = platform_name
            self.tag = tag # 非常重要，用于区分数据存储
            super().__init__(**kwargs)
            self.logger = crawler_logger.bind(platform=self.platform, tag=self.tag)
            # self.base_url = "..." # 定义基础 URL
            # self.content_type = "article" # 定义内容类型

        async def scrape(self, **kwargs):
            """爬取元数据"""
            self.logger.info("开始爬取元数据...")
            await self.async_init() # 初始化 Playwright 和浏览器
            # ... 实现具体的爬取逻辑 ...
            # 例如：导航到目标页面，解析元素，提取链接和标题
            # 使用 self.page 进行浏览器操作
            # await self.page.goto(self.base_url)
            # ...
            # 存储元数据，例如写入 JSON 文件或数据库
            self.logger.info("元数据爬取完成。")

        async def download_item(self, original_url, title, **kwargs):
            """下载单个项目的具体内容"""
            self.logger.debug(f"准备下载: {title} ({original_url})")
            # ... 实现下载逻辑 ...
            # 通常也需要 await self.async_init() 如果 scrape 后关闭了浏览器
            # 或者确保浏览器会话持续
            # await self.page.goto(original_url)
            # content = await self.page.content()
            # ... 保存内容 ...
            # self.save_data(data, filename_prefix=title)

        async def download(self, **kwargs):
            """根据已爬取的元数据下载完整内容"""
            self.logger.info("开始下载内容...")
            # 读取之前 scrape 保存的元数据列表
            # for item_metadata in metadata_list:
            #     await self.download_item(item_metadata['original_url'], item_metadata['title'])
            self.logger.info("内容下载完成。")

        async def login_for_cookies(self):
            """如果平台需要登录，实现此方法以获取和保存 Cookies"""
            self.logger.info("开始登录流程...")
            await self.async_init()
            # ... 实现登录逻辑 ...
            # 例如：导航到登录页，填充表单，点击登录按钮
            # 成功登录后，从 self.context.cookies() 获取 cookies
            # cookies = await self.context.cookies()
            # self.save_cookies(cookies) # 使用基类方法保存
            self.logger.info("登录完成并已保存 Cookies。")

    ```

2.  **实现必要方法**:
    *   `__init__(self, **kwargs)`: 初始化爬虫配置，**务必设置 `self.platform` 和 `self.tag`**，并调用 `super().__init__(**kwargs)`。
    *   `scrape(self, **kwargs)`: 主爬取方法，负责抓取元数据。
    *   `download(self, **kwargs)`: 根据元数据下载完整内容。可以进一步细分为 `download_item` 等方法。
    *   `login_for_cookies(self)`: 如果需要登录才能访问数据，则必须实现此方法。

3.  **数据保存**:
    爬取的原始数据应保存在 `data/raw/<platform>/<tag>/` 目录下。推荐使用 JSON 格式，并遵循模块 `README.md` 中建议的字段规范。基类提供了 `self.safe_write_file(path, content)` 方法用于安全写入文件。

## 注意事项

*   **速率限制与反爬**:
    *   生产环境 (大规模爬取) 请设置 `debug=False` 和 `headless=True`。
    *   调试模式 (`debug=True`) 通常会跳过一些随机延时和复杂的模拟用户行为，更容易触发反爬机制。
    *   合理使用 `await self.random_sleep()`（基类方法，但需在异步方法中 `await`）或 `asyncio.sleep()` 来控制请求频率。
    *   考虑使用代理 (`use_proxy=True`) 并配置有效的代理池。
*   **日志级别**: 项目配置要求，一般情况日志使用 `debug` 级别，只有最重要的信息采用 `info` 级别。通过 `self.logger.debug(...)` 和 `self.logger.info(...)` 使用。
*   **错误处理**: 在爬虫逻辑中妥善处理网络错误、元素找不到、解析错误等异常情况。
*   **资源关闭**: 确保在爬虫任务结束后调用 `await self.close()` 来正确关闭浏览器和释放 Playwright 资源，防止资源泄露。
*   **异步编程**: 爬虫模块大量使用 `asyncio` 和 `async/await` 语法，确保在调用异步方法时使用 `await`，并通过 `asyncio.run()` 来执行顶层异步函数。
*   **配置文件敏感信息**: 确保 `config.json` 中的敏感信息（如 token、账号密码）不要提交到公共代码库。可以使用 `.gitignore` 忽略该文件，并通过环境变量或其他安全方式管理生产环境配置。

## 调试技巧

*   **设置 `headless=False`**: 在开发初期，将 `headless` 设置为 `False` 可以看到浏览器界面的实际操作，方便定位问题。
*   **利用 `self.logger`**: 在关键步骤打印日志，了解执行流程和变量状态。
*   **Playwright Inspector**: Playwright 提供了 Inspector 工具，可以帮助调试和生成选择器。
    ```bash
    PWDEBUG=1 python -m etl.crawler.your_crawler
    ```
*   **逐步执行**: 将复杂的爬取流程分解为小步骤，逐个测试和验证。
*   **查看 `data/raw/` 目录**: 检查爬取的数据是否符合预期，文件名和内容是否正确。

## 现有爬虫模块简介

*   `wechat.py`: 爬取微信公众号文章。
*   `market.py`: 爬取校园集市（二手交易、活动等）数据。
*   `sina_finance.py`: 爬取新浪财经的相关数据。
*   `webpage_spider/`: 包含一个更通用的网页爬虫框架，可以配置化地爬取指定规则的网页。
*   `xhs_spider/`, `douyin_spider/`: 分别针对小红书和抖音平台的爬虫（具体实现细节需查看代码）。

通过本指南，希望能帮助您快速理解和使用 `etl/crawler` 模块。如有更复杂的需求或遇到问题，请参考模块内的 `README.md` 和具体爬虫的源代码。 