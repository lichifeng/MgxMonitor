'''
调用MgxParser可执行文件解析帝国时代II游戏存档。

传入的文件应该是已经被解压并验证过后缀名的帝国时代2游戏存档文件。
常见的后缀名是：['.mgx', '.mgx2', '.mgz', '.mgl', '.msx', '.msx2', '.aoe2record']
'''

import json
import subprocess
from mgxhub.config import cfg


def parse(file_path: str, opts: str = '') -> dict:
    '''
    调用 MgxParser 解析游戏存档文件。

    可以通过检查是否含有'guid'字段以及'status'的值来判断是否解析成功：
    - 'status'的值为'perfect'，并且含有'guid'字段。在MgxParser中，这代表存档的所有数据都被正常扫描过。
    - 'status'的值为'good'。在MgxParser中，这代表存档header部分的主要数据都被正常扫描过，至少能正常生成地图。
    - 'status'的值为'valid'。在MgxParser中，这代表存档的header和body部分能够被解压，但是解析过程出现问题。
    - 'status'的值为'invalid'。代表存档无效或无法解析，但是MgxParser能够正常工作。
    - 'status'的值为'error'。代表MgxParser返回了无效的JSON字符串，可能是由于参数错误或者其他原因。

    Args:
        file_path: str
            游戏存档文件的路径。

    Returns:
        dict
            解析后的游戏存档信息，是一个JSON对象。
    '''

    # 使用 subprocess.run 来运行命令并获取输出
    result = subprocess.run([cfg.get('system', 'parser'), file_path, opts], capture_output=True, text=True, check=False)

    # 尝试将输出解析为 JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {
            'status': 'error',
            'message': 'parsing failed in record_parser.py'
        }

    return data
