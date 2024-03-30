from pymongo import MongoClient
from tqdm import tqdm


def get_all_keys(doc, prefix=''):
    keys = set()
    for key, value in doc.items():
        if prefix:
            key = f'{prefix}.{key}'
        keys.add(key)
        if isinstance(value, dict):
            keys.update(get_all_keys(value, key))
    return keys


# 连接到MongoDB
mongo_client = MongoClient('mongodb://root:example@172.20.0.3:27017/')
mongo_db = mongo_client['mgxhub']
mongo_collection = mongo_db['records']

# 获取所有键
all_keys = set()
total_documents = mongo_collection.count_documents({})
for document in tqdm(mongo_collection.find(), total=total_documents):
    all_keys.update(get_all_keys(document))

# 打印结果
for key in sorted(all_keys):
    print(key)
