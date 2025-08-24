from scrapy import cmdline
import shutil
import os
print('子进程当前路径：',os.getcwd())
# 在启动命令前添加清理逻辑
shutil.rmtree('jobdir', ignore_errors=True)  # 先删除旧目录
if not os.path.exists('./log'):
    os.mkdir('./log')
cmdline.execute('scrapy crawl wikipieda_spider -s JOBDIR=jobdir  -s DEPTH_LIMIT=5'.split())