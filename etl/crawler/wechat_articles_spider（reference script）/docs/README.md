## 源码文件说明

| 文件名       | 功能                                       | 备注     |
| ------------ | ------------------------------------------ | -------- |
| AccountBiz   | 根据公众号名字得到Biz参数                  |          |
| ArticlesInfo | 根据文章链接获取文章具体信息，如阅读点赞等 |          |
| ArticlesUrls | 根据公众号名称获取最新或历史文章 | 需要个人信息，如cookie、token、key等         |
| Url2Html | 根据文章链接下载文章HTML至本地 | html离线可转换为word、pdf等其他可阅读格式         |
| ArticlesAPI  | 整合PublicAccountsWeb和ArticlesInfo        | 不再维护 |

## 代码变量的说明

|     变量名      |        说明        | 是否过期|
| :-------------: | :----------------: | :----------------:  |
| cookie | 这里包含多个平台的cookie，需要根据不同的方式在Headers中复制cookie参数 | 是|
|    token     |  同上，这个参数是在提交的表单中的token  |是|
|    appmsg_token     | 这个参数是在提交的表单中的，个人微信号的appmsg_token  |是|
| key | 多个平台个人信息的key | 是|
| uin | 个人微信号的uin |否，每个微信号独一无二的id|
| biz | 公众号的biz |否，每个公众号独一无二的id|
|comment_id| 获取评论的必要参数，在请求文章链接时获取 |否，对应于每篇文章|
|    nickname     |  需要获取文章的公众号名称  |否|
|    query     | 筛选公众号文章的关键词  |否|
| begin | 从第几篇文章开始爬取 |否|
| count | 每次爬取的文章数(最大为5, 但是返回结果可能会大于5) |否|

需要获取的参数均在文章中提及如何获取
