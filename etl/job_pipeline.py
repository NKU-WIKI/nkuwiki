from __init__ import *

from etl.transform.summarize_md import summarize_md
from etl.crawler.company_wechat import CompanyWechat

async def main():
    """异步主函数"""
    # company_crawler = CompanyWechat(debug=True, headless=True, use_proxy=True)
    # try:
    #     await company_crawler.async_init()
    #     await company_crawler.scrape(max_article_num=10, total_max_article_num=1e10)
    #     await company_crawler.download()
    # finally:
    #     # 确保资源正确关闭
    #     await company_crawler.close()
    input_dir = 'D:/code/nkuwiki/etl/data/raw/wechat/company'  # 指定JSON文件所在目录
    output_dir = 'D:/code/nkuwiki/etl/data/summary/'  
    # # 获取当前日期
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_date = datetime.strptime('2025-03-09', '%Y-%m-%d')
    # 使用不会产生空格问题的标题
    title = '2025大厂实习-春招-社招-官方信息汇总'
    header_text = 'nkuwiki提示您，信息均来自官方公众号，但摘要由AI生成，仅供参考，详情请点击原文链接。\n获取更多招聘信息请关注nkuwiki，持续为您更新~'
    summarize_md(input_dir, output_dir, (current_date,current_date), title=title, header_text=header_text)

if __name__ == '__main__':
    asyncio.run(main())

