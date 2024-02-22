import os
import mysql.connector


class DBHandler:

    _db_conn = None
    _mysql_host = None
    _mysql_port = None
    _mysql_user = None
    _mysql_password = None
    _mysql_database = None

    def __init__(
        self,
        host: str = None,
        port: str = None,
        user: str = None,
        password: str = None,
        database: str = None
    ):
        # 从环境变量或初始化参数获取数据库配置
        self._mysql_host = host or os.getenv('MYSQL_HOST')
        self._mysql_port = port or os.getenv('MYSQL_PORT')
        self._mysql_user = user or os.getenv('MYSQL_USER')
        self._mysql_password = password or os.getenv('MYSQL_PASSWORD')
        self._mysql_database = database or os.getenv('MYSQL_DATABASE')

    def __del__(self):
        if self._db_conn:
            self._db_conn.close()

    @property
    def db_conn(self):
        '''Get a connection to the database'''
        if not self._db_conn or not self._db_conn.is_connected():
            self._db_conn = mysql.connector.connect(
                user=self._mysql_user,
                password=self._mysql_password,
                host=self._mysql_host,
                port=self._mysql_port,
                database=self._mysql_database)
        return self._db_conn

    def init_tables(self):
        '''Use DB_TABLE_CREATION.sql to create tables'''
        with open('DB_TABLE_CREATION.sql', 'r') as f:
            sql = f.read()
            cursor = self.db_conn.cursor()
            cursor.execute(sql)
            cursor.close()

    def _insert_chat(self, raw_data: dict):
        '''Insert chat data into the database'''

        if not 'chat' in raw_data and isinstance(raw_data['chat'], list):
            return

        chats = []
        for chat in raw_data['chat']:
            chats.append((
                raw_data.get('guid', ''),
                raw_data.get('recPlayer', None),
                chat.get('time', 0),
                chat.get('msg', '')
            ))

        query = ("INSERT INTO chat (game_guid, recorder, chat_time, chat_content) "
                 "VALUES (%s, %s, %s, %s)")
        cursor = self.db_conn.cursor()
        cursor.executemany(query, chats)
        cursor.close()

    def _insert_files(
            self,
            raw_data: dict,
            filename: str,
            last_modified: int,
            notes: str = ''
    ):
        '''Insert file data into the database'''

        query = ("INSERT INTO files (game_guid, md5, recorder, parser, parse_time, parsed_status, raw_filename, raw_lastmodified, notes) "
                 "VALUES (%s, %s, %s, %s)")
        cursor = self.db_conn.cursor()
        cursor.execute(
            query, (
                raw_data.get('guid', ''),
                raw_data.get('md5', ''),
                raw_data.get('recPlayer', None),
                raw_data.get('parser', None),
                raw_data.get('parseTime', 0),
                raw_data.get('status', 'unknown'),
                filename,
                last_modified,
                notes
            ))
        cursor.close()
