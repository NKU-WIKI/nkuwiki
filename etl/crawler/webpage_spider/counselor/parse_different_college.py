from bs4 import BeautifulSoup
import lxml.etree as etree

url_maps = {
    '文学院': 'http://wxy.nankai.edu.cn/', '历史学院': 'http://history.nankai.edu.cn/',
    '哲学院': 'http://phil.nankai.edu.cn/', '外国语学院': 'https://sfs.nankai.edu.cn/',
    '法学院': 'http://law.nankai.edu.cn/', '周恩来政府管理学院': 'http://zfxy.nankai.edu.cn/',
    '马克思主义学院': 'http://cz.nankai.edu.cn/', '汉语言文化学院': 'http://hyxy.nankai.edu.cn/',
    '经济学院': 'http://economics.nankai.edu.cn/', '商学院': 'http://bs.nankai.edu.cn/',
    '旅游与服务学院': 'http://tas.nankai.edu.cn/', '金融学院': 'http://finance.nankai.edu.cn/',
    '数学科学学院': 'http://math.nankai.edu.cn/', '物理科学学院': 'http://physics.nankai.edu.cn/',
    '化学学院': 'http://chem.nankai.edu.cn/', '生命科学学院': 'http://sky.nankai.edu.cn/',
    '环境科学与工程学院': 'http://env.nankai.edu.cn/', '医学院': 'http://medical.nankai.edu.cn/',
    '药学院': 'http://pharmacy.nankai.edu.cn/', '电子信息与光学工程学院': 'http://ceo.nankai.edu.cn/',
    '材料科学与工程学院': 'http://mse.nankai.edu.cn/', '计算机学院': 'http://cc.nankai.edu.cn/',
    '密码与网络空间安全学院': 'http://cyber.nankai.edu.cn/', '人工智能学院': 'http://ai.nankai.edu.cn/',
    '软件学院': 'http://cs.nankai.edu.cn/', '统计与数据科学学院': 'http://stat.nankai.edu.cn/',
    '新闻与传播学院': 'https://jc.nankai.edu.cn/', '社会学院': 'https://shxy.nankai.edu.cn/',
    '南开大学新闻网': 'https://news.nankai.edu.cn/', '南开大学': 'https://www.nankai.edu.cn/',
    '陈省身数学研究所': 'http://www.cim.nankai.edu.cn/', '组合数学中心': 'https://cfc.nankai.edu.cn/',
    '生物质资源化利用国家地方联合工程研究中心': 'https://nrcb.nankai.edu.cn/',
    '学生就业指导中心': 'https://career.nankai.edu.cn/', '南开大学教务部': 'https://jwc.nankai.edu.cn/',
    '南开大学研究生院': 'https://graduate.nankai.edu.cn/', '南开大学科学技术研究部': 'https://std.nankai.edu.cn/',
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
    '南开数学百年': 'http://century.math.nankai.edu.cn/', '日本研究院': 'http://www.riyan.nankai.edu.cn/',

    '功能材料与能源化学创新团队': 'https://energy.nankai.edu.cn/', '医学院（英文）': 'http://en.medical.nankai.edu.cn',
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

    '南开大学财务信息网':'https://cwc.nankai.edu.cn/',
    '南开大学机构知识库':'http://ir.nankai.edu.cn/',
    '南开大学接待中心':'https://nkjd.nankai.edu.cn/',
    '商学院（ibs）':'https://ibs.nankai.edu.cn/',
    '中国大学生物理学术竞赛':'https://pt.nankai.edu.cn/',
    '前沿光子学与声学微结构研究组':'https://chenlab.nankai.edu.cn/',
    'The Zhiqiang Niu Group Lab of Aqueous Battery':'http://www.niu.nankai.edu.cn/',
    '南开大学招投标管理办公室':'https://nkzbb.nankai.edu.cn/',
    '商学院专业学位中心':'https://mba.nankai.edu.cn/'
}
url_maps_urls = [i.replace('http://', '').replace('https://', '')[:-1] for i in url_maps.values()]

def get_pushtime_from_url(url: str):
    """
    支持解析的示例，https://21cnmarx.nankai.edu.cn/2023/1030/c16905a526941/page.htm
    """
    pattern = r'(\d{4})/(\d{2})(\d{2})/'
    match = re.search(pattern, url)
    if match:
        year, month, day = match.groups()
        date_str = f"{year}-{month}-{day}"
        # print(date_str)  # 输出：2023-10-30
    return date_str

def parse_function(ans, url: str):
    """
    解析网页内容
    """


    if "https://chem.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//div[@class="page-news-title"]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//div[@class="page-news-souse"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://chem.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://chem.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img


    elif "https://news.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="root"]/table[3]/tbody/tr/td[1]/table[2]/tbody/tr[1]/td/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="root"]/table[3]/tbody/tr/td[1]/table[2]/tbody/tr[2]/td/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('td', attrs={'id': 'txt'})
        content = t.text if t else ''

        img = tree.xpath('//img[@border="0"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://news.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://news.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://history.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div/div/h1[1]/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath('/html/body/div[2]/div/div[2]/div[1]/span/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//div[@class="page-news-souse"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('/html/body/div[2]/div/div/div/div/p[1]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://history.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://history.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    # 研究生网
    elif 'yzb.nankai.edu.cn' in url:
        tree = etree.HTML(ans)
        title = tree.xpath('/html/body/div[2]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//span[@class="arti-update"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = ''

        return title, pushtime, content, img

    elif "https://zfxy.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div/div[2]/form/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//div[@class="con_wzsz"]/h3/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'v_news_content'})
        content = t.text if t else ''

        img = tree.xpath('//img[@class="img_vsb_content"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://zfxy.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://zfxy.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://phil.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://phil.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://phil.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://bs.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div/div/div[1]/h2/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath('/html/body/div[4]/div/div/div[1]/h2/span/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//div[@class="d"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('/html/body/div[4]/div/div/div[2]/div[1]/div[1]/text()')
            pushtime = pushtime[0].strip() if pushtime else None
            if not pushtime:
                pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://bs.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://bs.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://cet.neea.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="ReportIDname"]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="ReportIDIssueTime"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('span', attrs={'id': 'ReportIDtext'})
        content = t.text if t else ''

        img = ''
        return title, pushtime, content, img

    # 如果是CIM陈所，则需要另外一种解析方式
    elif 'cim.nankai.edu.cn/' in url:
        tree = etree.HTML(ans)
        # 提取标题
        title = tree.xpath('//*[@id="container2"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container2"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = ''
        return title, pushtime, content, img
    elif 'nim.nankai.edu.cn/' in url:
        tree = etree.HTML(ans)
        # 提取标题
        title = tree.xpath('//*[@id="container2"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container2"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = ''
        return title, pushtime, content, img

    elif "https://sfs.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://sfs.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://sfs.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://jwc.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//div[@class="page-news-title"]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//div[@class="page-news-souse"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = ''

        # 是否是PDF文件
        pdf = b.find('div', attrs={'class': "wp_pdf_player"})
        if pdf is not None:
            pdf = 'https://jwc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "//math.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="root"]/table[3]/tbody/tr/td[1]/table[2]/tbody/tr[1]/td/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="root"]/table[3]/tbody/tr/td[1]/table[2]/tbody/tr[2]/td/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
            pushtime = pushtime[0].strip() if pushtime else None
        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('td', attrs={'id': 'txt'})
        content = t.text if t else ''
        if content == '':
            t = b.find('div', attrs={'class': 'wp_articlecontent'})
            content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://math.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://math.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img


    # 如果是CIM陈所，则需要另外一种解析方式
    elif 'cim.nankai.edu.cn/' in url:
        tree = etree.HTML(ans)
        # 提取标题
        title = tree.xpath('//*[@id="container2"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container2"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@class="img_vsb_content"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://cim.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://cim.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif "https://wxy.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath('//h1[@class="arti_title"]/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//span[@class="arti_update"]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = ''

        return title, pushtime, content, img

    elif "https://tas.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[5]/form/hgroup/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[5]/form/hgroup/p/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'v_news_content'})
        content = t.text if t else ''

        img = tree.xpath('//img[@class="img_vsb_content"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://tas.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://tas.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://hyxy.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[2]/form/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div[2]/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'v_news_content'})
        content = t.text if t else ''

        img = tree.xpath('//img[@border="0"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://hyxy.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://hyxy.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://law.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://law.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://law.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://physics.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div[2]/div/div[2]/div/div/div/h1/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div[2]/div/div[2]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://physics.nankai.edu.cn/' + img

        return title, pushtime, content, img

    elif "https://sky.nankai.edu.cn" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[3]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://sky.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://sky.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

        # 研究生网
    elif 'yzb.nankai.edu.cn' in url:
        tree = etree.HTML(ans)
        title = tree.xpath('/html/body/div[2]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div/div/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = ''
        return title, pushtime, content, img

    elif "https://economics.nankai.edu.cn/" in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div[2]/div[1]/div[1]/div/div[1]/span/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[4]/div[2]/div[1]/div[1]/div/div[2]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://economics.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://economics.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://finance.nankai.edu.cn/" in url:

        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div[2]/div[1]/div[1]/div/div[1]/span/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[4]/div[2]/div[1]/div[1]/div/div[2]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            pushtime = tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div/div[2]/div[1]/div/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://finance.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://finance.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf

        return title, pushtime, content, img

    elif "https://cz.nankai.edu.cn/" in url:

        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div[2]/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div[2]/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@border="0"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://cz.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://cz.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://21cnmarx.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div/div[4]/div[2]/div[2]/div/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div[2]/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            pushtime = get_pushtime_from_url(url)
        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://21cnmarx.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://21cnmarx.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://medical.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[1]/div[4]/div/div[2]/div/div[2]/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[1]/div[4]/div/div[2]/div/div[2]/div[1]/div/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://medical.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://medical.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://tourism2011.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://tourism2011.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://tourism2011.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://sklmcb.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://sklmcb.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://sklmcb.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://env.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://env.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://env.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://www.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[1]/div[5]/div/div[2]/div[2]/div/div[2]/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[1]/div[5]/div/div[2]/div[2]/div/div[2]/div[2]/div[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://www.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://www.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://graduate.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div/div[2]/div[2]/div[2]/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div/div[2]/div[2]/div[2]/div[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://graduate.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://graduate.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://std.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@class="Article_Title"]/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath(
                '//*[@id="container_content"]/table/tbody/tr/td[2]/table/tbody/tr/td[2]/table[2]/tbody/tr/td/span/span/span/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath(
            '//*[@id="container_content"]/table/tbody/tr/td[2]/table/tbody/tr/td[2]/table[4]/tbody/tr/td/span[1]/span/span/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//span[@frag="窗口4"]/span/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://std.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://std.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://rsc.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div/div[4]/div[2]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div/div[4]/div[2]/div/div/div/p/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://rsc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://rsc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://cyber.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'data-eleid': "2"})
        content = t.text if t else ''
        if content == '':
            t = b.find('div', attrs={'class': "wp_articlecontent"})
            content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://cyber.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://cyber.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'https://mse.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://mse.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://mse.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'pharmacy.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://pharmacy.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://pharmacy.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'http://ceo.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://ceo.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://ceo.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'cc.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://cc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://cc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'http://ai.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://ai.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://ai.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'stat.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None
        if title is None:
            title = tree.xpath('//*[@id="container1"]/div/div/h1/text()')
            title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//*[@id="container1"]/div/div/p/span[2]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://stat.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://stat.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://jc.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://jc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://jc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://shxy.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//div[@class="con_wzsz"]/h3/span[2]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://shxy.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://shxy.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'http://www.cim.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://www.cim.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://www.cim.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://cfc.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if pushtime is None:
            pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://cfc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://cfc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://nrcb.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://nrcb.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://nrcb.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://career.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        xpath_list = [
            '/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()',
            '//div[@class="laiyuan"]/text()',
            '//p[@class="con_time"]/text()',
            '//div[@class="zpxx"]/text()',
            '/html/body/div[3]/div[2]/div/div[2]/div[1]/div[4]/text()'
        ]

        pushtime = None
        for xpath in xpath_list:
            result = tree.xpath(xpath)
            if result:
                pushtime = result[0].strip()
                break
        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "neirong"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://career.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://career.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://jcjd.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://jcjd.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://jcjd.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://taslab.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://taslab.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://taslab.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'skleoc.nankai.edu.cn' in url or 'en-skleoc.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://skleoc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://skleoc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://cec.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://cec.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://cec.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://klfpm.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://klfpm.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://klfpm.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'https://aemc.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/div/div[1]/div/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://aemc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://aemc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'www.riyan.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://www.riyan.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://www.riyan.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'century.math.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://century.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://century.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'swsyzx.nankai.edu.cn' in url:
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div[1]/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[1]/div/div[2]/div[1]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://swsyzx.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://swsyzx.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'energy.nankai.edu.cn' in url:
        # 功能材料与能源化学创新团队
        tree = etree.HTML(ans)
        b = BeautifulSoup(ans, 'lxml')
        # 提取标题
        title = tree.xpath('/html/body/div/div[6]/div[2]/div/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = b.find('div', class_='time time1')
        pushtime = pushtime.text if pushtime else None
        if not pushtime:
            pushtime = b.find('div', class_='time')
            pushtime = pushtime.text if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "paperIn"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://energy.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://energy.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.medical.nankai.edu.cn' in url:
        # 医学院（英文）
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[1]/div[4]/div/div[2]/div/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[1]/div[4]/div/div[2]/div/div[1]/div/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        if not pushtime:
            # 提取发布时间
            pushtime = tree.xpath('//div[@class="date"]/text()')
            pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.medical.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.medical.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.economics.nankai.edu.cn' in url:
        # 经济学院（英文）
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="subfield"]/div/div[2]/div/p[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="subfield"]/div/div[2]/div/p[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.economics.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.economics.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'binhai.nankai.edu.cn' in url:
        # 滨海开发研究院
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[2]/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[2]/div[1]/time/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://binhai.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://binhai.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'international.nankai.edu.cn' in url:
        # 南开大学国际合作与交流处、港澳台事务办公室、孔子学院工作办公室
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="main-content"]/article/h4/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="main-content"]/article/h6/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://international.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://international.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'lebps.nankai.edu.cn' in url:
        # 经济行为与政策模拟实验室
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://lebps.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://lebps.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.nankai.edu.cn' in url:
        # 南开大学（英文）
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[1]/div[3]/div/div/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[1]/div[3]/div/div/div[1]/div/text()')
        pushtime = pushtime[0].strip() if pushtime else None
        if not pushtime:
            # 提取发布时间
            pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://en.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://en.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        if not img:
            img = b.find('video')
            img = img.get('src') if img else None
            if img:
                if 'http' not in img:
                    img = 'https://en.nankai.edu.cn/' + img
        return title, pushtime, content, img
    elif 'tyb.nankai.edu.cn' in url:
        # 南开大学体育部
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div[2]/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div[2]/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://tyb.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://tyb.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'fy.nankai.edu.cn' in url:
        # 南开大学附属医院
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://fy.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://fy.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'bioinformatics.nankai.edu.cn' in url:
        # 南开大学生物信息学实验室
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://bioinformatics.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://bioinformatics.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ndst.nankai.edu.cn' in url:
        # 天津市网络与数据安全技术重点实验室
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="l-container"]/div/div/div[2]/div/div[2]/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="l-container"]/div/div/div[2]/div/div[2]/div/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ndst.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ndst.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'jsfz.nankai.edu.cn' in url:
        # 教师发展中心
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/h1[1]/span/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div[1]/span[1]/span/span/span/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "Article_Content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://jsfz.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://jsfz.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.stat.nankai.edu.cn' in url:
        # 统计与数据科学学院（英文）
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/main/div/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/main/div/div/div/div/p/span/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.stat.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.stat.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'aiguo.nankai.edu.cn' in url:
        # 南开大学爱国主义教育基地
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="wp_content_w6_0"]/p[1]/strong/span/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('///text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'data-eleid': "2"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://aiguo.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://aiguo.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ensfs.nankai.edu.cn' in url:
        # 外国语学院（英文）
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'data-eleid': "2"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ensfs.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ensfs.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'chemen.nankai.edu.cn' in url:
        # 化学学院（英文）
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div/div[4]/div/div/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div/div[4]/div/div/div[1]/div/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'data-eleid': "2"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://chemen.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://chemen.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'chinaeconomy.nankai.edu.cn' in url:
        # 中国特色社会主义经济建设协同创新中心
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//div[@class="cintent_main"]/table//font/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[2]/table//td/text()/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'data-eleid': "2"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://chinaeconomy.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://chinaeconomy.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'nkuaa.nankai.edu.cn' in url:
        # 南开校友\
        # 参考链接 https://nkuaa.nankai.edu.cn/info/1093/8303.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="newdetail_title"]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="newdetail_title"]/p/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://nkuaa.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://nkuaa.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'enven.nankai.edu.cn' in url:
        # 环境科学与工程学院（英文）\
        # 参考链接 https://enven.nankai.edu.cn/2024/1119/c19687a556781/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="l-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="l-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://enven.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://enven.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'yzb.nankai.edu.cn' in url:
        # 南开大学研究生招生网\
        # 参考链接 https://yzb.nankai.edu.cn/2024/1008/c5508a552564/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//span[@class="arti-update"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://yzb.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://yzb.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'hq.nankai.edu.cn' in url:
        # 南开大学后勤保障服务\
        # 参考链接 https://hq.nankai.edu.cn/2025/0102/c23997a561128/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://hq.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://hq.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'museum.nankai.edu.cn' in url:
        # 南开大学博物馆\
        # 参考链接 https://museum.nankai.edu.cn/2020/0930/c8626a304310/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://museum.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://museum.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ccsh.nankai.edu.cn' in url:
        # 南开大学中国社会史研究中心\
        # 参考链接 https://ccsh.nankai.edu.cn/2020/1001/c21843a304708/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ccsh.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ccsh.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'tedabio.nankai.edu.cn' in url:
        # 泰达生物技术研究院\
        # 参考链接 https://tedabio.nankai.edu.cn/2024/1206/c4643a558396/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="info"]/div/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="info"]/div/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://tedabio.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://tedabio.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ces.nankai.edu.cn' in url:
        # 政治经济学研究中心\
        # 参考链接 https://ces.nankai.edu.cn/2024/0913/c8424a550861/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container3"]/div/div[2]/div/div[2]/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container3"]/div/div[2]/div/div[2]/div/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ces.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ces.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'guard.nankai.edu.cn' in url:
        # 党委保卫部、保卫处\
        # 参考链接 https://guard.nankai.edu.cn/2023/0928/c10127a521310/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://guard.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://guard.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.sky.nankai.edu.cn' in url:
        # 生命科学学院（英文）\
        # 参考链接 http://en.sky.nankai.edu.cn/2023/0228/c7953a505295/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="infomain"]/div[2]/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="infomain"]/div[2]/div/p/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.sky.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.sky.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'apec.nankai.edu.cn' in url:
        # 亚太经济合作组织研究中心\
        # 参考链接 https://apec.nankai.edu.cn/2024/0102/c6564a534629/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="s5_component_wrap_inner"]/div[2]/div/div/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="s5_component_wrap_inner"]/div[2]/div/div/dl/dd/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://apec.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://apec.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ifd.nankai.edu.cn' in url:
        # 金融发展研究院\
        # 参考链接 https://ifd.nankai.edu.cn/2018/0529/c2816a100135/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ifd.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ifd.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.history.nankai.edu.cn' in url:
        # 历史学院（英文）\
        # 参考链接 http://en.history.nankai.edu.cn/2023/1129/c22217a530163/page.psp
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.history.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.history.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.mwhrc.nankai.edu.cn' in url:
        # 现代世界历史研究中心（英文）\
        # 参考链接 http://en.mwhrc.nankai.edu.cn/2020/1211/c21686a325722/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.mwhrc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.mwhrc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'gh.nankai.edu.cn' in url:
        # 南开大学工会\
        # 参考链接 https://gh.nankai.edu.cn/2025/0113/c3126a561766/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://gh.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://gh.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'teda.nankai.edu.cn' in url:
        # 泰达学院\
        # 参考链接 https://teda.nankai.edu.cn/2022/0607/c1709a456666/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//span[@class="Article_Title"]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//span[@class="Article_PublishDate"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://teda.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://teda.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'econlab.nankai.edu.cn' in url:
        # 经济实验教学中心\
        # 参考链接 https://econlab.nankai.edu.cn/2020/0928/c10483a303334/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div/div/div[1]/div[2]/div/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[4]/div/div/div[1]/div[2]/div/div[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://econlab.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://econlab.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'en.math.nankai.edu.cn' in url:
        # 数学科学学院（英文）\
        # 参考链接 http://en.math.nankai.edu.cn/2015/1106/c4036a31758/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div[1]/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div[1]/div/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.math.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.math.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'etc.env.nankai.edu.cn' in url:
        # 环境科学与工程实验教学中心\
        # 参考链接 http://etc.env.nankai.edu.cn/2023/1123/c2672a529304/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://etc.env.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://etc.env.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'kexie.nankai.edu.cn' in url:
        # 南开大学科学技术协会\
        # 参考链接 https://kexie.nankai.edu.cn/2024/0723/c6065a547754/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//td[@class="biaoti3"]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//span[@class="STYLE2"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://kexie.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://kexie.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'xnjj.nankai.edu.cn' in url:
        # 虚拟经济与管理研究中心\
        # 参考链接 https://xnjj.nankai.edu.cn/2021/1213/c28262a421438/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//a[@class="font14"]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('///text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://xnjj.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://xnjj.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'nbjl.nankai.edu.cn' in url:
        # 南开-百度联合实验室\
        # 参考链接 https://nbjl.nankai.edu.cn/2023/0716/c12124a516405/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="content"]/p/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('///text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://nbjl.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://nbjl.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'entas.nankai.edu.cn' in url:
        # 旅游与服务学院（英文）\
        # 参考链接 https://entas.nankai.edu.cn/info/1002/1978.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/form/hgroup/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[4]/form/hgroup/p/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://entas.nankai.edu.cn/index.htm' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://entas.nankai.edu.cn/index.htm' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'iap.nankai.edu.cn' in url:
        # 泰达应用物理研究院\
        # 参考链接 https://iap.nankai.edu.cn/2021/0617/c5145a373242/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://iap.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://iap.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'en.finance.nankai.edu.cn' in url:
        # 金融学院（英文）\
        # 参考链接 http://en.finance.nankai.edu.cn/2024/0910/c22564a551035/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div/div[2]/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div/div[2]/div[1]/div/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://en.finance.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://en.finance.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'jwcold.nankai.edu.cn' in url:
        # 教务处（旧版）\
        # 参考链接 https://jwcold.nankai.edu.cn/2024/0522/c20a543539/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://jwcold.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://jwcold.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'zzb.nankai.edu.cn' in url:
        # 教务处（旧版）\
        # 参考链接 https://zzb.nankai.edu.cn/2025/0121/c7416a562029/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div[2]/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div[2]/div/p/span/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://jwcold.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://jwcold.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'lib.nankai.edu.cn' in url:
        # 南开大学图书馆\
        # 参考链接 https://lib.nankai.edu.cn/2024/1011/c11990a552784/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        xpath_list = [
            '//*[@id="d-container"]/div/div/div/p/span[1]/text()',
            '//*[@id="d-container"]/div/div/div/p/span[2]/text()'
        ]

        pushtime = None
        for xpath in xpath_list:
            result = tree.xpath(xpath)
            if result:
                pushtime = result[0].strip()
                break
        if not pushtime:
            pushtime = get_pushtime_from_url(url)
        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://lib.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://lib.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        if not img:
            img = b.find('video')
            img = img.get('src') if img else None
            if img:
                if 'http' not in img:
                    img = 'https://lib.nankai.edu.cn/' + img

        return title, pushtime, content, img
    elif 'imo.nankai.edu.cn' in url:
        # 现代光学研究所\
        # 参考链接 https://imo.nankai.edu.cn/info/1054/1728.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="vsb_content"]/div/p[1]/strong/span/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('///text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://imo.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://imo.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'mwhrc.nankai.edu.cn' in url:
        # 世界近现代史研究中心\
        # 参考链接 https://mwhrc.nankai.edu.cn/2025/0113/c21543a561771/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://mwhrc.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://mwhrc.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'lac.nankai.edu.cn' in url:
        # 南开大学实验动物中心\
        # 参考链接 https://lac.nankai.edu.cn/2024/1219/c11944a559986/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://lac.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://lac.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'enlib.nankai.edu.cn' in url:
        # Nankai University Library\
        # 参考链接 https://enlib.nankai.edu.cn/2021/1008/c25583a400610/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "wp_articlecontent"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://enlib.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://enlib.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        if not img:
            img = b.find('video')
            img = img.get('src') if img else None
            if img:
                if 'http' not in img:
                    img = 'https://lib.nankai.edu.cn/' + img
        return title, pushtime, content, img

    elif 'nkuef.nankai.edu.cn' in url:
        # 天津南开大学教育基金会网站\
        # 参考链接 https://nkuef.nankai.edu.cn/info/1012/8048.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="wrapper"]/section[2]/div/div/div[1]/form/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="wrapper"]/section[2]/div/div/div[1]/form/p[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': "v_news_content"})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'http://nkuef.nankai.edu.cn' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'http://nkuef.nankai.edu.cn' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'pec.nankai.edu.cn' in url:
        # 南开大学物理实验中心\
        # 参考链接 https://pec.nankai.edu.cn/2025/0102/c12102a561129/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div[2]/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('///text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://pec.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://pec.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'dbis.nankai.edu.cn' in url:
        # 南开大学数据库与信息系统实验室\
        # 参考链接 https://dbis.nankai.edu.cn/2023/0212/c12145a504308/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="content"]/article/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('///text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://dbis.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://dbis.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'nkie.nankai.edu.cn' in url:
        # 南开经济研究所\
        # 参考链接 https://nkie.nankai.edu.cn/2020/0320/c11718a267589/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[2]/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[2]/div[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://nkie.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://nkie.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ssrm.nankai.edu.cn' in url:
        # 南开大学人文社会科学研究部\
        # 参考链接 https://ssrm.nankai.edu.cn/info/1012/3950.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="main"]/div[4]/form/div[2]/div[1]/h2/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="main"]/div[4]/form/div[2]/dl/dd[1]/time/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'v_news_content'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ssrm.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ssrm.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'dxwl.nankai.edu.cn' in url:
        # 大学基础物理\
        # 参考链接 https://dxwl.nankai.edu.cn/2014/0512/c1419a85805/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//title/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//span[@class="Article_PublishDate"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://dxwl.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://dxwl.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'tjphysics.nankai.edu.cn' in url:
        # 天津物理学会\
        # 参考链接 https://tjphysics.nankai.edu.cn/2023/1021/c783a525467/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//title/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//span[@class="Article_PublishDate"]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://tjphysics.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://tjphysics.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img


    elif 'encyber.nankai.edu.cn' in url:
        # 网络安全学院（英文）\
        # 参考链接 https://encyber.nankai.edu.cn/2023/1225/c34753a533301/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="d-container"]/div/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="d-container"]/div/div/div/p/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://encyber.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://encyber.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    #  其他类型的网站
    elif 'https://mp.weixin.qq.com/s' in url:
        b = BeautifulSoup(ans, 'lxml')
        title = b.find('h1')
        title = title.text if title else None

        # 提取发布时间
        pushtime = b.find('em', attrs={'id': 'publish_time'})
        pushtime = pushtime.text if pushtime else None

        # 提取内容
        content = b.find('div', attrs={'id': 'js_content'})
        content = content.text if content else None

        img = ''

        return title, pushtime, content, img
    elif 'cwc.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://cwc.nankai.edu.cn/2024/0625/c3303a546246/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="container"]/div/div[2]/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div[2]/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://cwc.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://cwc.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    
    elif 'ir.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 http://ir.nankai.edu.cn/Home/Author/9f74b526-5be0-4418-ad5f-a4154e533f79.html
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="body"]/div[2]/div[2]/div[1]/div[1]/div[1]/a/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="container"]/div/div[2]/div/p/span[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'pt10  pos'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ir.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ir.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'nkjd.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://nkjd.nankai.edu.cn/info/1014/2205.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[4]/div[2]/form/div/h1[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[4]/div[2]/form/div/div[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'v_news_content'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://nkjd.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://nkjd.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'ibs.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://ibs.nankai.edu.cn/n/3945.html
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="pageIntro"]/div[1]/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('//*[@id="pageIntro"]/div[2]/span[2]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'para-Content'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://ibs.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://ibs.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'pt.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://pt.nankai.edu.cn/2018/0204/c8520a89959/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//*[@id="info"]/div/div[2]/div/div/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//div[@class="img_wrapper"]/img')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://pt.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://pt.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    
    elif 'chenlab.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://chenlab.nankai.edu.cn/2019/0703/c24516a368504/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//title/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//div[@class="img_wrapper"]/img')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://chenlab.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://chenlab.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'www.niu.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://chenlab.nankai.edu.cn/2019/0703/c24516a368504/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//title/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'wp_articlecontent'})
        content = t.text if t else ''

        img = tree.xpath('//div[@class="img_wrapper"]/img')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://www.niu.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://www.niu.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    elif 'nkzbb.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://chenlab.nankai.edu.cn/2019/0703/c24516a368504/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('/html/body/div[3]/div/div[1]/h1/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = tree.xpath('/html/body/div[3]/div/div[1]/div/i[1]/text()')
        pushtime = pushtime[0].strip() if pushtime else None

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'ccontent'})
        content = t.text if t else ''

        img = tree.xpath('//div[@class="img_wrapper"]/img')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://nkzbb.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://nkzbb.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img

    elif 'mba.nankai.edu.cn' in url:
        # 南开大学财务信息网
        # 参考链接 https://mba.nankai.edu.cn/2020/0219/c19339a265404/page.htm
        tree = etree.HTML(ans)

        # 提取标题
        title = tree.xpath('//title/text()')
        title = title[0].strip() if title else None

        # 提取发布时间
        pushtime = get_pushtime_from_url(url)

        # 提取内容
        b = BeautifulSoup(ans, 'lxml')
        t = b.find('div', attrs={'class': 'ccontent'})
        content = t.text if t else ''

        img = tree.xpath('//img[@data-layer="photo"]')
        img = img[0].get('src') if img else None
        if img:
            if 'http' not in img:
                img = 'https://mba.nankai.edu.cn/' + img

        if (img is None) and (content.replace('\xa0', '') == ''):
            pdf = b.find('div', attrs={'class': "wp_pdf_player"})
            if pdf is not None:
                pdf = 'https://mba.nankai.edu.cn/' + pdf.get('pdfsrc')
            img = pdf
        return title, pushtime, content, img
    raise Exception(f'没有对应的解析规则。url = {url}')


# 被遗弃的netlocs们

['old.lib.nankai.edu.cn',
 'bbs.nankai.edu.cn',
 'less.nankai.edu.cn',
 'mem.nankai.edu.cn',
 'physics.nankai.edu.cn',
 '100.nankai.edu.cn',
 'nkuefnew.nankai.edu.cn',
 'nkda.nankai.edu.cn',
 'yanglab.nankai.edu.cn',
 'fzs.nankai.edu.cnsky.nankai.edu.cn',
 'fzs.nankai.edu.cnlife.less.nankai.edu.cn',
 'jss.nankai.edu.cn',
 'icia.nankai.edu.cn',
 'shsj.nankai.edu.cn',
 'zixiuke.nankai.edu.cn',
 'ygb.nankai.edu.cn',
 'oldphysics.nankai.edu.cn',
 'english.nankai.edu.cn',
 'recruitment.nankai.edu.cn',
 'phys.nankai.edu.cn',
 'waizhuan.nankai.edu.cn',
 'sms.nankai.edu.cn',
 'it.nankai.edu.cn',
 'libprint.lib.nankai.edu.cn',
 'opac.nankai.edu.cn',
 'ic.lib.nankai.edu.cn',
 'www.tianjinforum.nankai.edu.cn',
 'chempaper.nankai.edu.cn',
 'libprint.nankai.edu.cn',
 'nktv.nankai.edu.cn',
 'hqbzb.nankai.edu.cn',
 'zhaoqizheng.nkbinhai.nankai.edu.cn',
 'zhouliqun.nkbinhai.nankai.edu.cn',
 'radio.nankai.edu.cn',
 'keji.nankai.edu.cn',
 'sheke.nankai.edu.cn',
 'jw.nankai.edu.cn',
 'fcollege.nankai.edu.cn',
 'en.fcollege.nankai.edu.cn',
 'www.zk-nankai.com',
 'iam.nankai.edu.cn',
 'cim-profile.nankai.edu.cn',
 'base_url',
 'xxgk.nankai.edu.cn',
 'careers.nankai.edu.cn',
 'cyber-backend.nankai.edu.cn',

 # 以下是可以访问但是没有什么实际内容的网站
 'phy.less.nankai.edu.cn',
 'env.less.nankai.edu.cn',
 'med.less.nankai.edu.cn',
 'sklmcb.less.nankai.edu.cn']
