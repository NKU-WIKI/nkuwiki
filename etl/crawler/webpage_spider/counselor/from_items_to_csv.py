import pandas as pd

data = {
    '标题':[],
    '内容':[],
    'url':[],
    'push_time':[],
    'content':[],
    'file_url':[]
}
#             counselor_item['content_entity'] = content_entity.replace(':Category', '')
#             counselor_item['category'] = '\t'.join(cates)
#             counselor_item['time'] = str(time.time())
#             counselor_item['url'] = this_url
#             counselor_item['content'] = str(content_page)

with open('items.jsonl','r',encoding='utf8') as e:
    import json
    data_raw = [json.loads(a) for a in e.readlines()]



num = 0
for d in data_raw:
    if d['content'] == '':
        continue
    if num>1000:
        break
    data['标题'].append(d['content_entity'])
    data['内容'].append(d['content'])
    data['url'].append(d['url'])
    # data['分类'].append(Traditional2Simplified(d['category']))
    num+=1

print('总数据量：',len(data_raw))
df = pd.DataFrame(data)
df = df.drop_duplicates()
print('去重后：',df.shape[0])
df.to_excel('汇总结果.xlsx',index=False)