import asyncio
from datetime import datetime
from etl import RAW_PATH
from etl.crawler.wechat import Wechat
from etl.crawler import company_accounts
from etl.processors import summarize_markdown_file as summarize_md
from etl.utils.const import recruitment_keywords

async def main():
    """异步主函数"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    # current_date = datetime.strptime('2025-03-13', '%Y-%m-%d')
    job_crawler = Wechat(authors=company_accounts, tag = "job", debug=True, headless=True, use_proxy=True)
    try:
        await job_crawler.async_init()
        await job_crawler.scrape(max_article_num=10, total_max_article_num=1e10, time_range=(current_date, current_date), recruitment_keywords=recruitment_keywords)
        await job_crawler.page.close()
        await job_crawler.context.clear_cookies()
    finally:
        await job_crawler.context.new_page()
        await job_crawler.download(time_range=(current_date, current_date), bot_tag="job")
        await job_crawler.close()
    input_dir = RAW_PATH / 'wechat' / 'job'  # 指定JSON文件所在目录
    output_dir = RAW_PATH / 'summary' 
    # 使用不会产生空格问题的标题
    title = '2025大厂实习/春招/社招/官方信息汇总'
    header_text = 'nkuwiki提示您，信息均来自官方公众号，但摘要由AI生成，仅供参考，详情请点击原文链接。\n获取更多招聘信息请关注nkuwiki，持续为您更新~'
    summarize_md(input_dir, output_dir, (current_date,current_date), title=title, header_text=header_text)

# 0 18 * * * cd /home/nkuwiki/nkuwiki && /opt/venvs/nkuwiki/bin/python -m etl.job_pipeline
if __name__ == '__main__':
    asyncio.run(main())

