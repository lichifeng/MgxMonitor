import hashlib
import os
import shutil
import tempfile
import time
import zipfile
from datetime import datetime

import requests
from pymongo import MongoClient
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from tqdm import tqdm

MONGO_URI = 'mongodb://mongo_2sar8m:mongo_cMKpkK@localhost/'
RECORDS_DIR = '/records'
API_URL = 'https://aocrecapi.dl.y2b.cc/game/upload'
API_URL_SERVER_STATUS = 'https://aocrecapi.dl.y2b.cc/'
SERVER_SAPCE_LIMIT = 100  # in GB

# 定义数据库名
database_name = f"migrate_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"

# 创建SQLite数据库引擎
engine = create_engine(f'sqlite:///{database_name}')

# 创建ORM基类
Base = declarative_base()


class Log(Base):
    # 定义Log表
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    guid = Column(String)
    srcfile = Column(String)
    mongid = Column(String)
    md5 = Column(String)
    found = Column(DateTime)
    updated = Column(DateTime)
    gametime = Column(DateTime)
    status = Column(Integer)
    message = Column(String)


# 创建表
Base.metadata.create_all(engine)

# 创建Session
Session = sessionmaker(bind=engine)
session = Session()

# 检查 exception 文件夹是否存在，如果不存在就创建它
exception_dir = os.path.join(os.getcwd(), 'exception')
os.makedirs(exception_dir, exist_ok=True)

# 连接MongoDB数据库
client = MongoClient(MONGO_URI)
mongodb = client.mgxhub
records_collection = mongodb.records


# 创建临时目录
temp_dir = tempfile.mkdtemp()


# 遍历records_dir目录下的每个文件
N = 1000  # 每N个文件打包成一个压缩包
files_to_zip = []
queued_logs = []

# 服务器的空余空间
server_free_space = requests.get(API_URL_SERVER_STATUS, timeout=30).json()['disk'][0]  # in GB

# 创建一个tqdm对象
pbar = tqdm(os.listdir(RECORDS_DIR))
for entry in pbar:
    pbar.set_description(f'Disk space: {server_free_space}GB')
    while server_free_space < SERVER_SAPCE_LIMIT:
        sleep_time = 60
        while sleep_time > 0:
            pbar.set_description(f'Low space: {server_free_space}GB. Sleeping {sleep_time}s.')
            time.sleep(1)
            sleep_time -= 1
        server_free_space = requests.get(API_URL_SERVER_STATUS, timeout=30).json()['disk'][0]

    md5_result = None
    message = None
    # 检查是否达到了N个文件
    if len(files_to_zip) >= N:
        # 创建ZIP文件
        zip_filename = f'batch_{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'
        zip_filepath = os.path.join(temp_dir, zip_filename)
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in files_to_zip:
                zip_file.write(file, arcname=os.path.basename(file))

        # 发送到API
        with open(zip_filepath, 'rb') as file_to_upload:
            size = os.path.getsize(zip_filepath)
            size_mb = round(size / (1024 * 1024), 2)

            # 更新进度条的描述信息
            pbar.set_description(f'Uploading {entry} ({size_mb} MB)...')

            files = {'recfile': file_to_upload}
            response = requests.post(
                API_URL,
                files=files,
                timeout=120,
                auth=('username', 'password')
            )

        # 将queued_logs中的日志写入数据库
        for log_entry in queued_logs:
            session.add(log_entry)
        session.commit()
        queued_logs = []

        # 删除临时目录中的文件
        for file in files_to_zip:
            os.remove(file)
        os.remove(zip_filepath)

        # 清空待打包列表
        files_to_zip = []

        # 更新服务器的空余空间
        server_free_space = requests.get(API_URL_SERVER_STATUS, timeout=30).json()['disk'][0]

    filepath = os.path.join(RECORDS_DIR, entry)
    if os.path.isfile(filepath) and entry.endswith('.zip'):
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                # 解压zip文件到临时目录
                zip_ref.extractall(temp_dir)
                # 获取解压缩的文件列表
                extracted_files = zip_ref.namelist()

                # 检查列表是否为空
                if not extracted_files:
                    raise Exception('The ZIP file is empty.')

                # 获取第一个文件
                extracted_file = extracted_files[0]

                extracted_path = os.path.join(temp_dir, extracted_file)

                # 计算解压出来的文件的md5
                with open(extracted_path, 'rb') as file_to_check:
                    data = file_to_check.read()
                    md5_result = hashlib.md5(data).hexdigest()

                # 查找records集合中的文档
                record = records_collection.find_one({'files.md5': md5_result})
                if record:
                    # 修改解压后文件的修改日期
                    if 'gameTime' in record:
                        gametime = record['gameTime']
                        # 如果 gameTime 早于 1999 年，使用当前时间
                        if gametime.year < 1999:
                            gametime = datetime.now()
                        os.utime(extracted_path, (gametime.timestamp(), gametime.timestamp()))
                    else:
                        pass

                    # 重命名文件
                    if 'legacy' in record and 'filenames' in record['legacy']:
                        if record['legacy']['filenames']:
                            new_filename1 = max(record['legacy']['filenames'], key=len)
                    if 'files' in record:
                        if record['files']:
                            new_filename2 = max(record['files'], key=lambda x: len(x['filename']))['filename']
                    if new_filename1 and new_filename2:
                        new_filename = max(new_filename1, new_filename2, key=len)
                    else:
                        message = message + '\rNo filename found in the Mongodb.'
                        new_filename = extracted_file

                    new_filepath = os.path.join(temp_dir, new_filename)
                    if new_filepath in files_to_zip:
                        base, ext = os.path.splitext(new_filepath)
                        suffix = 1
                        while f"{base}_{suffix}{ext}" in files_to_zip:
                            suffix += 1
                        new_filepath = f"{base}_{suffix}{ext}"
                    os.rename(extracted_path, new_filepath)

                    # 添加文件到待打包列表
                    files_to_zip.append(new_filepath)

                    # 记录日志
                    # 保存到SQLite数据库
                    if not 'lastUpdated' in record:
                        updated = datetime.now()
                    else:
                        updated = record['lastUpdated']

                    if not 'firstFound' in record:
                        found = datetime.now()
                    else:
                        found = record['firstFound']

                    if 'guid' in record:
                        guid = record['guid']

                    log_entry = Log(srcfile=entry, mongid=str(record['_id']), md5=md5_result,
                                    found=found, updated=updated,
                                    gametime=gametime, status=None, message=message, guid=guid)
                    queued_logs.append(log_entry)

                else:
                    # 文件存到exception文件夹下
                    exception_path = os.path.join(exception_dir, entry)
                    shutil.move(filepath, exception_path)

                    # 数据库里保存一条相应的信息
                    log_entry = Log(srcfile=entry, md5=md5_result, status=None, message='File not found in MongoDB.')
                    session.add(log_entry)
                    session.commit()
        except Exception as e:
            # 文件存到exception文件夹下
            exception_path = os.path.join(exception_dir, entry)
            shutil.move(filepath, exception_path)

            # 记录错误信息
            log_entry = Log(srcfile=entry, md5=md5_result, status=None, message=str(e))
            session.add(log_entry)
            session.commit()

# 处理剩余的文件
if files_to_zip:
    # 创建ZIP文件
    zip_filename = f'batch_{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'
    zip_filepath = os.path.join(temp_dir, zip_filename)
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files_to_zip:
            zip_file.write(file, arcname=os.path.basename(file))

    # 发送到API
    with open(zip_filepath, 'rb') as file_to_upload:
        files = {'recfile': file_to_upload}
        # lastmod = datetime.fromtimestamp(os.path.getmtime(zip_filepath)).isoformat()
        # data = {'lastmod': lastmod}
        # response = requests.post(API_URL, files=files, data=data, auth=('username', 'password'))
        response = requests.post(
            API_URL,
            files=files,
            auth=('username', 'password'),
            timeout=120
        )

    # 将queued_logs中的日志写入数据库
    for log_entry in queued_logs:
        session.add(log_entry)
    session.commit()
    queued_logs = []

    # 删除临时目录中的文件
    for file in files_to_zip:
        os.remove(file)
    os.remove(zip_filepath)

# 删除临时目录
shutil.rmtree(temp_dir)

# 获取总数
total = records_collection.count_documents({})

# 遍历records集合中的每个文档的files字段
for record in tqdm(records_collection.find(), total=total):
    for file in record.get('files', []):
        md5_value = file.get('md5')
        if md5_value and not session.query(Log).filter_by(md5=md5_value).first():
            # 新增记录到SQLite数据库
            log_entry = Log(
                mongid=str(record['_id']), md5=md5_value,
                status=None, message='MD5 not found in SQLite.')
            session.add(log_entry)
            session.commit()

# 关闭数据库连接
session.close()
