import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl import *
from etl.crawler import *
from etl.crawler.wechat import Wechat
from etl.transform.summarize_md import summarize_md

recruitment_keywords = [
    # 基础招聘术语
    '招聘', '职位', '岗位', '应聘', '求职', '校招', '社招', '实习', '人才', '简历', 
    # 招聘类型
    '校园招聘', '企业招聘', '全球招聘', '秋季招聘', '春季招聘', '暑期招聘', '专场招聘',
    # 需求表述
    '人才需求', '用人需求', '招人', '招募', '诚招', '急招', '热招', '高薪招', '直招',
    # 机会表述
    '就业机会', '工作机会', '职业机会', '发展机会', '就业机会', '就业信息',
    # 正式或委婉表述
    '招贤纳士', '诚聘', '虚位以待', '求贤若渴', '纳贤', '聘用', '聘请',
    # 英文关键词
    'job', 'career', 'hire', 'recruit', 'employment', 'position', 'opportunity',
    # 招聘活动
    '招聘会', '宣讲会', '双选会', '招聘活动', '线上招聘', '现场招聘',
    # 招聘流程相关
    '面试', 'offer', '入职', '简历投递', '笔试', '面试官', '笔试题', '招聘流程',
    # 福利待遇相关
    '薪资', '待遇', '福利', '五险一金', '年终奖', '奖金', '补贴', '津贴',
    # 求职者相关
    '毕业生', '应届生', '毕业', '学历', '研究生', '本科', '硕士', '博士',
    # 行业特定术语
    '猎头', 'HR', '人力资源', '用人单位', '招工',
    # 模糊相关词
    '加入', '加盟', '加入我们', '团队扩招', '扩招', '寻找', '寻'
]
async def main():
    """异步主函数"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    # current_date = datetime.strptime('2025-03-10', '%Y-%m-%d')
    job_crawler = Wechat(authors=COMPANY_ACCOUNTS, tag = "job", debug=True, headless=True, use_proxy=True)
    try:
        await job_crawler.async_init()
        await job_crawler.scrape(max_article_num=10, total_max_article_num=1e10, time_range=(current_date, current_date), recruitment_keywords=recruitment_keywords)
        await job_crawler.download(time_range=(current_date, current_date), bot_tag="job")
    finally:
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

