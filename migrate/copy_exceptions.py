# GPT generated script not revised yet.

import os
import shutil

from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.orm import sessionmaker

# 创建SQLite数据库引擎
engine = create_engine('sqlite:///migrate_20240411190857.db')

# 创建Session
Session = sessionmaker(bind=engine)
session = Session()

# 获取log表的元数据
metadata = MetaData()
log_table = Table('log', metadata, autoload_with=engine)

# 查询所有message不为空的记录
query = select(log_table).where(log_table.c.message != None)
results = session.execute(query)

# 创建exceptions文件夹
exceptions_dir = os.path.join(os.getcwd(), 'exception')
os.makedirs(exceptions_dir, exist_ok=True)

# 复制文件
for result in results:
    srcfile = result['srcfile']
    if srcfile:
        dstfile = os.path.join(exceptions_dir, srcfile)
        shutil.copyfile(f"/records/{srcfile}", dstfile)
