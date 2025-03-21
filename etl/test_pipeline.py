import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl import *
from etl.crawler import *
from etl.crawler.wechat import Wechat
from etl.transform.summarize_md import summarize_md
requerment_keywords=[]

async def main():
    """异步主函数"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    from_date = datetime.strptime('2025-03-01', '%Y-%m-%d')
    crawler = Wechat(authors=UNIVERSITY_OFFICIAL_ACCOUNTS + SCHOOL_OFFICIAL_ACCOUNTS, tag = "nku", debug=True, headless=True, use_proxy=True)
    # try:
        # await crawler.async_init()
        # await crawler.scrape(max_article_num=10, total_max_article_num=1e10, time_range=(from_date, current_date), recruitment_keywords=None)
        # await crawler.page.close()
        # await crawler.context.clear_cookies()
    # finally:
        # await crawler.context.new_page()
    await crawler.download(time_range=(from_date, current_date), bot_tag="knowledge")
    await crawler.close()
    input_dir = RAW_PATH / 'wechat' / 'nku'  # 指定JSON文件所在目录
    output_dir = RAW_PATH / 'summary' 
    title = '南开大学活动信息汇总'
    header_text = 'nkuwiki提示您，信息均来自官方公众号，但摘要由AI生成，仅供参考，详情请点击原文链接。\n获取更多活动信息请关注nkuwiki，持续为您更新~'
    summarize_md(input_dir, output_dir, (current_date,current_date), title=title, header_text=header_text,requerment_keywords=requerment_keywords)

# 0 18 * * * cd /home/nkuwiki/nkuwiki && /opt/venvs/nkuwiki/bin/python -m etl.job_pipeline
if __name__ == '__main__':
    asyncio.run(main())

