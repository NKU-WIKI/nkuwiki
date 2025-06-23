"""
南开大学相关常量定义
包含域名映射、微信公众号分类等常量
"""

# 域名到来源的映射字典
domain_source_map = {
    'news.nankai.edu.cn': '南开大学新闻网',
    'phil.nankai.edu.cn': '南开大学哲学院',
    'medical.nankai.edu.cn': '南开大学医学院（英文）',
    'www.nankai.edu.cn': '南开大学',
    'en.nankai.edu.cn': '南开大学（英文）',
    'en.medical.nankai.edu.cn': '南开大学医学院（英文）',
    'chem.nankai.edu.cn': '南开大学化学学院',
    'chemen.nankai.edu.cn': '南开大学化学学院（英文）',
    'mse.nankai.edu.cn': '南开大学材料科学与工程学院',
    'enven.nankai.edu.cn': '南开大学环境科学与工程学院（英文）',
    'tourism2011.nankai.edu.cn': '南开大学现代旅游业发展协同创新中心',
    'weekly.nankai.edu.cn': '南开大学新闻网',
    'sklmcb.nankai.edu.cn': '南开大学药物化学生物学国家重点实验室',
    'math.nankai.edu.cn': '南开大学数学科学学院',
    'physics.nankai.edu.cn': '天津物理学会',
    'iap.nankai.edu.cn': '南开大学泰达应用物理研究院',
    'law.nankai.edu.cn': '南开大学法学院',
    'international.nankai.edu.cn': '南开大学国际合作与交流处、港澳台事务办公室、孔子学院工作办公室',
    'graduate.nankai.edu.cn': '南开大学研究生院',
    'jwc.nankai.edu.cn': '南开大学教务部',
    'jcjd.nankai.edu.cn': '南开大学高校思想政治理论课马克思主义基本原理概论教材研究基地',
    '21cnmarx.nankai.edu.cn': '南开大学21世纪马克思主义研究院',
    'cz.nankai.edu.cn': '南开大学马克思主义学院',
    'finance.nankai.edu.cn': '南开大学金融学院（英文）',
    'bs.nankai.edu.cn': '南开大学商学院',
    'en.finance.nankai.edu.cn': '南开大学金融学院（英文）',
    'env.nankai.edu.cn': '南开大学环境科学与工程实验教学中心',
    'ces.nankai.edu.cn': '南开大学政治经济学研究中心',
    'economics.nankai.edu.cn': '南开大学经济学院（英文）',
    'chinaeconomy.nankai.edu.cn': '南开大学中国特色社会主义经济建设协同创新中心',
    'econlab.nankai.edu.cn': '南开大学经济实验教学中心',
    'apec.nankai.edu.cn': '南开大学亚太经济合作组织研究中心',
    'xnjj.nankai.edu.cn': '南开大学虚拟经济与管理研究中心',
    'lebps.nankai.edu.cn': '南开大学经济行为与政策模拟实验室',
    'nrcb.nankai.edu.cn': '南开大学生物质资源化利用国家地方联合工程研究中心',
    'etc.env.nankai.edu.cn': '南开大学环境科学与工程实验教学中心',
    'taslab.nankai.edu.cn': '南开大学旅游与服务学院旅游实验教学中心',
    'en.economics.nankai.edu.cn': '南开大学经济学院（英文）',
    'cfc.nankai.edu.cn': '南开大学组合数学中心',
    'stat.nankai.edu.cn': '南开大学统计与数据科学学院（英文）',
    'history.nankai.edu.cn': '南开大学历史学院（英文）',
    'sky.nankai.edu.cn': '南开大学生命科学学院（英文）',
    'swsyzx.nankai.edu.cn': '南开大学生物国家级实验教学示范中心',
    'tedabio.nankai.edu.cn': '南开大学泰达生物技术研究院',
    'en.sky.nankai.edu.cn': '南开大学生命科学学院（英文）',
    'en.history.nankai.edu.cn': '南开大学历史学院（英文）',
    'century.nankai.edu.cn': '南开数学百年',
    'en.math.nankai.edu.cn': '南开大学数学科学学院（英文）',
    'sfs.nankai.edu.cn': '南开大学外国语学院（英文）',
    'ensfs.nankai.edu.cn': '南开大学外国语学院（英文）',
    'std.nankai.edu.cn': '南开大学科学技术研究部',
    'rsc.nankai.edu.cn': '南开大学人事处',
    'webplus3.nankai.edu.cn': '南开大学新闻与传播学院',
    'bioinformatics.nankai.edu.cn': '南开大学生物信息学实验室',
    'jc.nankai.edu.cn': '南开大学新闻与传播学院',
    'ndst.nankai.edu.cn': '南开大学天津市网络与数据安全技术重点实验室',
    'fy.nankai.edu.cn': '南开大学附属医院',
    'hq.nankai.edu.cn': '南开大学后勤保障服务',
    'aiguo.nankai.edu.cn': '南开大学爱国主义教育基地',
    'kexie.nankai.edu.cn': '南开大学科学技术协会',
    'jwcold.nankai.edu.cn': '南开大学教务处（旧版）',
    'tas.nankai.edu.cn': '南开大学现代旅游业发展协同创新中心',
    'www.riyan.nankai.edu.cn': '南开大学日本研究院',
    'jsfz.nankai.edu.cn': '南开大学教师发展中心',
    'tyb.nankai.edu.cn': '南开大学体育部',
    'museum.nankai.edu.cn': '南开大学博物馆',
    'ccsh.nankai.edu.cn': '南开大学中国社会史研究中心',
    'guard.nankai.edu.cn': '南开大学党委保卫部、保卫处',
    'gh.nankai.edu.cn': '南开大学工会',
    'en.mwhrc.nankai.edu.cn': '南开大学现代世界历史研究中心（英文）',
    'teda.nankai.edu.cn': '南开大学泰达学院',
    'nbjl.nankai.edu.cn': '南开-百度联合实验室',
    'lac.nankai.edu.cn': '南开大学实验动物中心',
    'encyber.nankai.edu.cn': '南开大学网络安全学院（英文）',
    'nkie.nankai.edu.cn': '南开经济研究所',
    'mwhrc.nankai.edu.cn': '南开大学世界近现代史研究中心',
    'pec.nankai.edu.cn': '南开大学物理实验中心',
    'tjphysics.nankai.edu.cn': '天津物理学会',
    'dbis.nankai.edu.cn': '南开大学数据库与信息系统实验室',
    'lib.nankai.edu.cn': '南开大学图书馆（英文）',
    'yzb.nankai.edu.cn': '南开大学研究生招生网',
    'nkbinhai.nankai.edu.cn': '南开大学滨海开发研究院'
}

# 非官方微信公众号
unofficial_accounts = ["我们在听", "南开校园帮", "天南情报站", "我门难开"]

# 大学官方微信公众号
university_official_accounts = [
    "南开大学", "南开大学教务部", "南开大学图书馆", "南开大学学生创新创业", "南开体育之声", 
    "平安南开园", "南开学生会组织", "南开就业", "南开大学生", "南开微学工", "南开本科招生", 
    "南开大学团委", "活力南开", "全球南开师生交流", "南开大学体育场馆管理中心", "南开大学一卡通"
]

# 学院官方微信公众号
school_official_accounts = [
    "南开大学文学院", "南开文院人", "南开史学", "南开大学哲学院", "南开大学法学院", "NKULaw那些事儿", 
    "NKULaw学生会", "南开大学政府学院", "周政青年", "周政学生", "NK外院", "南开大学经济学院", 
    "南开大学经院e学工", "南开大学金融学院", "南开大学金融学院学工在线", "南开大学商学院", "南开商青年", 
    "南开马院", "南开大学旅游与服务学院", "NKU汉院", "NK数院", "南开物理", "NKPhysics", "南开化学", 
    "NK化学家南开生物", "南开电光之家", "NK人工智能", "NKU计算机", "NKU网安", "南开大学泰达学院", 
    "南开大学软件学院", "南开环境", "南开大学医学院", "南开医学生", "南开大学药学院", "南开材料", 
    "南开大学统计与数据科学学院", "统院拾光"
]

# 社团官方微信公众号
club_official_accounts = [
    "南开大学激扬排球俱乐部", "南开爱乐", "nk新觉悟", "周池之家", "翰墨留香", "南开大学翔宇剧社", 
    "南开国乐", "南开大学国乐相声协会", "NKUMUN海棠国际关系学会", "南开文博考古", "NKU红学社", 
    "NK职协", "南开学生立公研究会", "南开爱心", "南开花道社", "NKU武术小筑", "NK摄影与无人机社团", 
    "南大街舞", "南开飞扬无限轮滑社", "NK推理", "瑚琏琴社", "南开大学电影协会", "新长城NKU自强社", 
    "南开思源社", "南开大学红十字会", "南开跑协NKURunning", "南开演讲团", "南开融通", "nku越艺社", 
    "红与紫", "南开法援", "NKUIO", "3D打印南开", "南开多隆", "南开VR社", "创新技术学生俱乐部", 
    "南开羽协", "NKUTIC", "Crazy4Programming", "NKUISA", "南开口琴爱好者联盟", "南开环境", 
    "南开心协", "binghuo", "丽泽书会", "南开民乐团", "南开主持", "南开甲子曲社", "公能思辩社", 
    "南开海风", "NKU咖啡浪潮俱乐部", "21世纪英文学社", "南开大学量化投资研究会", "小楠的飞盘日记", 
    "NKU外文剧社", "NKFA", "NKTennis", "NKU跆拳道社", "南开织音", "NK烽火篮球社", "南开经济初学社", 
    "NKU经管法20", "南开大学三农学社", "南开咨询俱乐部", "南开龙舟", "NKU诗联学会", "开镌文学社", 
    "南开物理思辨社", "南开绿行", "南开APEX", "NKU噜噜手作社", "南开钢琴社", "南开国标舞团", 
    "灵南科幻", "南开自然博物", "南开学生京剧团", "南开天协", "NKU射箭队", "南风动画学术结社之夏"
]

# 创建包含所有官方来源的列表并去重
# 包含domain_source_map所有值和university_official_accounts、school_official_accounts
official_author = list(set(list(domain_source_map.values()) + university_official_accounts + school_official_accounts))

# 所有公众号类型
all_accounts = {
    'unofficial': unofficial_accounts,
    'university_official': university_official_accounts,
    'school_official': school_official_accounts,
    'club_official': club_official_accounts
}

# 南开大学网站URL映射 - 基于scrapy爬虫的完整URL映射
nankai_url_maps = {
    '文学院': 'http://wxy.nankai.edu.cn/', 
    '历史学院': 'http://history.nankai.edu.cn/',
    '哲学院': 'http://phil.nankai.edu.cn/', 
    '外国语学院': 'https://sfs.nankai.edu.cn/',
    '法学院': 'http://law.nankai.edu.cn/', 
    '周恩来政府管理学院': 'http://zfxy.nankai.edu.cn/',
    '马克思主义学院': 'http://cz.nankai.edu.cn/', 
    '汉语言文化学院': 'http://hyxy.nankai.edu.cn/',
    '经济学院': 'http://economics.nankai.edu.cn/', 
    '商学院': 'http://bs.nankai.edu.cn/',
    '旅游与服务学院': 'http://tas.nankai.edu.cn/', 
    '金融学院': 'http://finance.nankai.edu.cn/',
    '数学科学学院': 'http://math.nankai.edu.cn/', 
    '物理科学学院': 'http://physics.nankai.edu.cn/',
    '化学学院': 'http://chem.nankai.edu.cn/', 
    '生命科学学院': 'http://sky.nankai.edu.cn/',
    '环境科学与工程学院': 'http://env.nankai.edu.cn/', 
    '医学院': 'http://medical.nankai.edu.cn/',
    '药学院': 'http://pharmacy.nankai.edu.cn/', 
    '电子信息与光学工程学院': 'http://ceo.nankai.edu.cn/',
    '材料科学与工程学院': 'http://mse.nankai.edu.cn/', 
    '计算机学院': 'http://cc.nankai.edu.cn/',
    '密码与网络空间安全学院': 'http://cyber.nankai.edu.cn/', 
    '人工智能学院': 'http://ai.nankai.edu.cn/',
    '软件学院': 'http://cs.nankai.edu.cn/', 
    '统计与数据科学学院': 'http://stat.nankai.edu.cn/',
    '新闻与传播学院': 'https://jc.nankai.edu.cn/', 
    '社会学院': 'https://shxy.nankai.edu.cn/',
    '南开大学新闻网': 'https://news.nankai.edu.cn/', 
    '南开大学': 'https://www.nankai.edu.cn/',
    '陈省身数学研究所': 'http://www.cim.nankai.edu.cn/', 
    '组合数学中心': 'https://cfc.nankai.edu.cn/',
    '生物质资源化利用国家地方联合工程研究中心': 'https://nrcb.nankai.edu.cn/',
    '学生就业指导中心': 'https://career.nankai.edu.cn/', 
    '南开大学教务部': 'https://jwc.nankai.edu.cn/',
    '南开大学研究生院': 'https://graduate.nankai.edu.cn/', 
    '南开大学科学技术研究部': 'https://std.nankai.edu.cn/',
    '南开大学人事处': 'https://rsc.nankai.edu.cn/',
    '南开大学高校思想政治理论课马克思主义基本原理概论教材研究基地': 'https://jcjd.nankai.edu.cn/',
    '南开大学21世纪马克思主义研究院': 'https://21cnmarx.nankai.edu.cn/',
    '南开大学旅游与服务学院旅游实验教学中心': 'https://taslab.nankai.edu.cn/',
    '南开大学现代旅游业发展协同创新中心': 'https://tourism2011.nankai.edu.cn/',
    '南开大学元素有机化学国家重点实验室': 'http://skleoc.nankai.edu.cn/',
    '药物化学生物学国家重点实验室': 'https://sklmcb.nankai.edu.cn/',
    '南开大学化学实验教学中心': 'https://cec.nankai.edu.cn/',
    '功能高分子材料教育部重点实验室': 'https://klfpm.nankai.edu.cn/',
    '先进能源材料化学教育部重点实验室': 'https://aemc.nankai.edu.cn/',
    '生物国家级实验教学示范中心': 'https://swsyzx.nankai.edu.cn/',
    '南开数学百年': 'http://century.math.nankai.edu.cn/', 
    '日本研究院': 'http://www.riyan.nankai.edu.cn/',
    '功能材料与能源化学创新团队': 'https://energy.nankai.edu.cn/', 
    '医学院（英文）': 'http://en.medical.nankai.edu.cn',
    '经济学院（英文）': 'http://en.economics.nankai.edu.cn/',
    '滨海开发研究院': 'http://binhai.nankai.edu.cn/',
    '南开大学国际合作与交流处、港澳台事务办公室、孔子学院工作办公室': 'https://international.nankai.edu.cn/',
    '经济行为与政策模拟实验室': 'https://lebps.nankai.edu.cn/',
    '南开大学（英文）': 'https://en.nankai.edu.cn/',
    '南开大学体育部': 'https://tyb.nankai.edu.cn/',
    '南开大学附属医院': 'https://fy.nankai.edu.cn/',
    '南开大学生物信息学实验室': 'https://bioinformatics.nankai.edu.cn/',
    '天津市网络与数据安全技术重点实验室': 'https://ndst.nankai.edu.cn/',
    '教师发展中心': 'https://jsfz.nankai.edu.cn/',
    '统计与数据科学学院（英文）': 'http://en.stat.nankai.edu.cn/',
    '南开大学爱国主义教育基地': 'https://aiguo.nankai.edu.cn/',
    '外国语学院（英文）': 'https://ensfs.nankai.edu.cn/',
    '化学学院（英文）': 'https://chemen.nankai.edu.cn/',
    '中国特色社会主义经济建设协同创新中心': 'https://chinaeconomy.nankai.edu.cn/',
    '南开校友': 'https://nkuaa.nankai.edu.cn/',
    '环境科学与工程学院（英文）': 'https://enven.nankai.edu.cn/',
    '南开大学研究生招生网': 'https://yzb.nankai.edu.cn/',
    '南开大学后勤保障服务': 'https://hq.nankai.edu.cn/',
    '南开大学博物馆': 'https://museum.nankai.edu.cn/',
    '南开大学中国社会史研究中心': 'https://ccsh.nankai.edu.cn/',
    '泰达生物技术研究院': 'https://tedabio.nankai.edu.cn/',
    '政治经济学研究中心': 'https://ces.nankai.edu.cn/',
    '党委保卫部、保卫处': 'https://guard.nankai.edu.cn/',
    '生命科学学院（英文）': 'http://en.sky.nankai.edu.cn/',
    '亚太经济合作组织研究中心': 'https://apec.nankai.edu.cn/',
    '金融发展研究院': 'https://ifd.nankai.edu.cn/',
    '历史学院（英文）': 'http://en.history.nankai.edu.cn/',
    '现代世界历史研究中心（英文）': 'http://en.mwhrc.nankai.edu.cn/',
    '南开大学工会': 'https://gh.nankai.edu.cn/',
    '泰达学院': 'https://teda.nankai.edu.cn/',
    '经济实验教学中心': 'https://econlab.nankai.edu.cn/',
    '数学科学学院（英文）': 'http://en.math.nankai.edu.cn/',
    '陈省身数学研究所（备用）': 'http://www.nim.nankai.edu.cn/',
    '环境科学与工程实验教学中心': 'http://etc.env.nankai.edu.cn/',
    '南开大学科学技术协会': 'https://kexie.nankai.edu.cn/',
    '虚拟经济与管理研究中心': 'https://xnjj.nankai.edu.cn/',
    '南开-百度联合实验室': 'https://nbjl.nankai.edu.cn/',
    '旅游与服务学院（英文）': 'https://entas.nankai.edu.cn/index.htm',
    '泰达应用物理研究院': 'https://iap.nankai.edu.cn/',
    '金融学院（英文）': 'http://en.finance.nankai.edu.cn/',
    '教务处（旧版）': 'https://jwcold.nankai.edu.cn/',
    '南开大学党委组织部': 'https://zzb.nankai.edu.cn/',
    '南开大学图书馆': 'https://lib.nankai.edu.cn/',
    '世界近现代史研究中心': 'https://mwhrc.nankai.edu.cn',
    '南开大学实验动物中心': 'https://lac.nankai.edu.cn',
    '南开大学图书馆（英文）': 'https://enlib.nankai.edu.cn',
    '天津南开大学教育基金会网站': 'https://nkuef.nankai.edu.cn',
    '南开大学物理实验中心': 'https://pec.nankai.edu.cn',
    '南开大学现代光学研究所': 'https://imo.nankai.edu.cn',
    '南开大学数据库与信息系统实验室': 'https://dbis.nankai.edu.cn',
    '南开经济研究所': 'https://nkie.nankai.edu.cn',
    '南开大学人文社会科学研究部': 'https://ssrm.nankai.edu.cn',
    '南开大学电子信息与光学工程学院': 'https://ceo.nankai.edu.cn',
    '大学基础物理': 'https://dxwl.nankai.edu.cn',
    '天津物理学会': 'https://tjphysics.nankai.edu.cn/',
    '网络安全学院（英文）': 'https://encyber.nankai.edu.cn/',
    '南开大学财务信息网': 'https://cwc.nankai.edu.cn/',
    '南开大学机构知识库': 'http://ir.nankai.edu.cn/',
    '南开大学接待中心': 'https://nkjd.nankai.edu.cn/',
    '商学院（ibs）': 'https://ibs.nankai.edu.cn/',
    '中国大学生物理学术竞赛': 'https://pt.nankai.edu.cn/',
    '前沿光子学与声学微结构研究组': 'https://chenlab.nankai.edu.cn/',
    'The Zhiqiang Niu Group Lab of Aqueous Battery': 'http://www.niu.nankai.edu.cn/',
    '南开大学招投标管理办公室': 'https://nkzbb.nankai.edu.cn/',
    '商学院专业学位中心': 'https://mba.nankai.edu.cn/'
}

# 扩展种子URL，提高网页发现效率
additional_seed_urls = [
    # 新闻网各栏目 - 扩展更多栏目
    'https://news.nankai.edu.cn/ywsd/',  # 要闻速递
    'https://news.nankai.edu.cn/mtjj/',  # 媒体聚焦
    'https://news.nankai.edu.cn/zhxw/',  # 综合新闻
    'https://news.nankai.edu.cn/kydt/',  # 科研动态
    'https://news.nankai.edu.cn/xsdt/',  # 学术动态
    'https://news.nankai.edu.cn/tbft/',  # 图片报道
    'https://news.nankai.edu.cn/xsfc/',  # 学术风采
    'https://news.nankai.edu.cn/ttxw/',  # 头条新闻
    
    # 主站所有主要栏目
    'https://www.nankai.edu.cn/nkyw/',   # 南开要闻
    'https://www.nankai.edu.cn/xshd/',   # 学术活动
    'https://www.nankai.edu.cn/tzgg/',   # 通知公告
    'https://www.nankai.edu.cn/xsdt/',   # 学术动态
    'https://www.nankai.edu.cn/rcpy/',   # 人才培养
    'https://www.nankai.edu.cn/kxyj/',   # 科学研究
    'https://www.nankai.edu.cn/shfw/',   # 社会服务
    'https://www.nankai.edu.cn/whjl/',   # 文化交流
    
    # 就业中心全面覆盖
    'https://career.nankai.edu.cn/zpxx/',  # 招聘信息
    'https://career.nankai.edu.cn/jydt/',  # 就业动态
    'https://career.nankai.edu.cn/download/', # 下载专区
    'https://career.nankai.edu.cn/jyzd/',  # 就业指导
    'https://career.nankai.edu.cn/cyzl/',  # 创业指导
    'https://career.nankai.edu.cn/gkx/',   # 公考信息
    
    # 教务处完整栏目
    'https://jwc.nankai.edu.cn/tzgg/',   # 通知公告
    'https://jwc.nankai.edu.cn/jwxw/',   # 教务新闻
    'https://jwc.nankai.edu.cn/bks/',    # 本科生
    'https://jwc.nankai.edu.cn/jxgl/',   # 教学管理
    'https://jwc.nankai.edu.cn/ksjw/',   # 考试教务
    'https://jwc.nankai.edu.cn/sjjx/',   # 实践教学
    
    # 研究生院全面覆盖
    'https://graduate.nankai.edu.cn/zsxx/', # 招生信息
    'https://graduate.nankai.edu.cn/pygl/', # 培养管理
    'https://graduate.nankai.edu.cn/xwgl/', # 学位管理
    'https://graduate.nankai.edu.cn/tzgg/', # 通知公告
    'https://graduate.nankai.edu.cn/xwdt/', # 新闻动态
    
    # 所有学院新闻和通知页面
    'https://cc.nankai.edu.cn/xwzx/',    # 计算机学院新闻中心
    'https://cc.nankai.edu.cn/tzgg/',    # 计算机学院通知公告
    'https://math.nankai.edu.cn/xwdt/',  # 数学学院新闻动态
    'https://math.nankai.edu.cn/tzgg/',  # 数学学院通知公告
    'https://physics.nankai.edu.cn/xwzx/', # 物理学院新闻中心
    'https://physics.nankai.edu.cn/tzgg/', # 物理学院通知公告
    'https://chem.nankai.edu.cn/xwzx/',  # 化学学院新闻中心
    'https://chem.nankai.edu.cn/tzgg/',  # 化学学院通知公告
    'https://economics.nankai.edu.cn/xwzx/', # 经济学院新闻中心
    'https://economics.nankai.edu.cn/tzgg/', # 经济学院通知公告
    'https://bs.nankai.edu.cn/xwzx/',    # 商学院新闻中心
    'https://bs.nankai.edu.cn/tzgg/',    # 商学院通知公告
    'https://law.nankai.edu.cn/xwzx/',   # 法学院新闻中心
    'https://law.nankai.edu.cn/tzgg/',   # 法学院通知公告
    'https://wxy.nankai.edu.cn/xwzx/',   # 文学院新闻中心
    'https://wxy.nankai.edu.cn/tzgg/',   # 文学院通知公告
    'https://history.nankai.edu.cn/xwzx/', # 历史学院新闻中心
    'https://history.nankai.edu.cn/tzgg/', # 历史学院通知公告
    'https://phil.nankai.edu.cn/xwzx/',  # 哲学院新闻中心
    'https://phil.nankai.edu.cn/tzgg/',  # 哲学院通知公告
    'https://sfs.nankai.edu.cn/xwzx/',   # 外国语学院新闻中心
    'https://sfs.nankai.edu.cn/tzgg/',   # 外国语学院通知公告
    'https://zfxy.nankai.edu.cn/xwzx/',  # 政府管理学院新闻中心
    'https://zfxy.nankai.edu.cn/tzgg/',  # 政府管理学院通知公告
    'https://cz.nankai.edu.cn/xwzx/',    # 马克思主义学院新闻中心
    'https://cz.nankai.edu.cn/tzgg/',    # 马克思主义学院通知公告
    'https://sky.nankai.edu.cn/xwzx/',   # 生命科学学院新闻中心
    'https://sky.nankai.edu.cn/tzgg/',   # 生命科学学院通知公告
    'https://env.nankai.edu.cn/xwzx/',   # 环境学院新闻中心
    'https://env.nankai.edu.cn/tzgg/',   # 环境学院通知公告
    'https://medical.nankai.edu.cn/xwzx/', # 医学院新闻中心
    'https://medical.nankai.edu.cn/tzgg/', # 医学院通知公告
    'https://ceo.nankai.edu.cn/xwzx/',   # 电子信息学院新闻中心
    'https://ceo.nankai.edu.cn/tzgg/',   # 电子信息学院通知公告
    'https://mse.nankai.edu.cn/xwzx/',   # 材料学院新闻中心
    'https://mse.nankai.edu.cn/tzgg/',   # 材料学院通知公告
    'https://cyber.nankai.edu.cn/xwzx/', # 网络安全学院新闻中心
    'https://cyber.nankai.edu.cn/tzgg/', # 网络安全学院通知公告
    'https://ai.nankai.edu.cn/xwzx/',    # 人工智能学院新闻中心
    'https://ai.nankai.edu.cn/tzgg/',    # 人工智能学院通知公告
    'https://cs.nankai.edu.cn/xwzx/',    # 软件学院新闻中心
    'https://cs.nankai.edu.cn/tzgg/',    # 软件学院通知公告
    'https://stat.nankai.edu.cn/xwzx/',  # 统计学院新闻中心
    'https://stat.nankai.edu.cn/tzgg/',  # 统计学院通知公告
    
    # 管理部门网站
    'https://rsc.nankai.edu.cn/tzgg/',   # 人事处通知公告
    'https://rsc.nankai.edu.cn/xwdt/',   # 人事处新闻动态
    'https://std.nankai.edu.cn/tzgg/',   # 科研部通知公告
    'https://std.nankai.edu.cn/xwdt/',   # 科研部新闻动态
    'https://international.nankai.edu.cn/tzgg/', # 国际交流处通知
    'https://international.nankai.edu.cn/xwdt/', # 国际交流处新闻
    'https://hq.nankai.edu.cn/tzgg/',    # 后勤保障通知
    'https://hq.nankai.edu.cn/xwdt/',    # 后勤保障新闻
    'https://cwc.nankai.edu.cn/tzgg/',   # 财务处通知
    'https://zzb.nankai.edu.cn/tzgg/',   # 组织部通知
    'https://gh.nankai.edu.cn/tzgg/',    # 工会通知
    
    # 档案和历史页面（增加覆盖深度）
    'https://news.nankai.edu.cn/zhxw/2024/',  # 2024年综合新闻
    'https://news.nankai.edu.cn/zhxw/2023/',  # 2023年综合新闻
    'https://news.nankai.edu.cn/zhxw/2022/',  # 2022年综合新闻
    'https://news.nankai.edu.cn/ywsd/2024/',  # 2024年要闻速递
    'https://news.nankai.edu.cn/ywsd/2023/',  # 2023年要闻速递
    'https://news.nankai.edu.cn/kydt/2024/',  # 2024年科研动态
    'https://news.nankai.edu.cn/kydt/2023/',  # 2023年科研动态
    
    # 专题网站和重要栏目
    'https://www.nankai.edu.cn/15894/list.htm',  # 南开要闻列表
    'https://www.nankai.edu.cn/15895/list.htm',  # 学术活动列表
    'https://www.nankai.edu.cn/15896/list.htm',  # 通知公告列表
    
    # 增加科研院所和中心
    'https://skleoc.nankai.edu.cn/',     # 元素有机化学国家重点实验室
    'https://sklmcb.nankai.edu.cn/',     # 药物化学生物学国家重点实验室
    'https://cfc.nankai.edu.cn/',        # 组合数学中心
    'https://energy.nankai.edu.cn/',     # 功能材料与能源化学创新团队
    'https://nkie.nankai.edu.cn/',       # 南开经济研究所
    'https://apec.nankai.edu.cn/',       # 亚太经济合作组织研究中心
    'https://ifd.nankai.edu.cn/',        # 金融发展研究院
    'https://xnjj.nankai.edu.cn/',       # 虚拟经济与管理研究中心
]

# 生成所有南开起始URL
nankai_start_urls = list(nankai_url_maps.values()) + additional_seed_urls
# 去重处理
nankai_start_urls = list(set(nankai_start_urls))

# ===== 爬虫相关常量 =====

# 公司微信公众号账号列表
company_accounts = [
    "字节跳动招聘", "腾讯招聘", "阿里巴巴集团招聘", "百度招聘", "美团招聘", "京东招聘",
    "网易招聘", "滴滴招聘", "小米招聘", "华为招聘", "OPPO招聘", "vivo招聘", "一加招聘",
    "比亚迪招聘", "理想汽车招聘", "蔚来招聘", "小鹏汽车招聘", "零跑汽车招聘",
    "中金公司招聘", "中信建投招聘", "国泰君安招聘", "海通证券招聘", "中信证券招聘",
    "招商银行招聘", "中国银行招聘", "工商银行招聘", "建设银行招聘", "农业银行招聘",
    "平安集团招聘", "中国人寿招聘", "太平洋保险招聘", "新华保险招聘",
    "万科招聘", "恒大集团招聘", "碧桂园招聘", "融创中国招聘", "保利发展招聘",
    "中石油招聘", "中石化招聘", "中海油招聘", "国家电网招聘", "中国电信招聘",
    "中国移动招聘", "中国联通招聘", "中国烟草招聘", "中国邮政招聘"
]

# 浏览器用户代理
default_user_agents = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.62",
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

# 爬虫配置
default_timezone = "Asia/Shanghai"
default_locale = "zh-CN"

# ===== 招聘关键词常量 =====

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

# ===== 数据处理常量 =====

# HTML和特殊字符处理模式
html_tags_pattern = r'<.*?>'
special_chars_pattern = r'[^\w\s\u4e00-\u9fff]'

# 文本长度限制
max_text_length = 1000000  # 最大文本长度
min_text_length = 10       # 最小文本长度

# 批处理大小
default_batch_size = 100
max_batch_size = 1000

# ===== 更新导出列表 =====

__all__ = [
    'domain_source_map',
    'unofficial_accounts',
    'university_official_accounts', 
    'school_official_accounts',
    'club_official_accounts',
    'company_accounts',
    'official_author',
    'all_accounts',
    'nankai_url_maps',
    'additional_seed_urls',
    'nankai_start_urls',
    # 爬虫相关
    'default_user_agents',
    'user_agents',
    'default_timezone',
    'default_locale',
    # 招聘相关
    'recruitment_keywords',
    # 数据处理
    'html_tags_pattern',
    'special_chars_pattern',
    'max_text_length',
    'min_text_length',
    'default_batch_size',
    'max_batch_size'
] 