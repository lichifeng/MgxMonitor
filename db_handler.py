import json
import time
from hashlib import md5
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from orm_models import Base, Game, Player, File, Chat, LegacyInfo, Ratings

start_time = time.time()

engine = create_engine("sqlite:///test_db.sqlite3", echo=False)
Base.metadata.create_all(engine)

# load test/sample_parsed_data.json, close the file after loaded
test_data = None
with open("test/sample_parsed_data.json", "r") as f:
    test_data = json.load(f)

# create a session
session = Session(engine)

# insert data into database
session.add(Game(
    game_guid=test_data.get('guid'),
    duration=test_data.get('duration'),
    include_ai=test_data.get('includeAI'),
    is_multiplayer=test_data.get('isMultiplayer'),
    population=test_data.get('population'),
    speed=test_data.get('speedEn'),
    matchup=test_data.get('matchup'),
    map_name=test_data.get('map', {}).get('nameEn'),
    map_size=test_data.get('map', {}).get('sizeEn'),
    version_code=test_data.get('version', {}).get('code'),
    version_log=test_data.get('version', {}).get('logVer'),
    version_raw=test_data.get('version', {}).get('rawStr'),
    version_save=test_data.get('version', {}).get('saveVer'),
    version_scenario=test_data.get('version', {}).get('scenarioVersion'),
    victory_type=test_data.get('victory', {}).get('typeEn'),
    source=test_data.get('source'),
    instruction=test_data.get('instruction'),
    game_time=datetime.fromisoformat(test_data.get('gameTime')),
    first_found=test_data.get('firstFound')
))

players = []
if 'players' in test_data and isinstance(test_data['players'], list):
    for p in test_data['players']:
        player_name = '<EMPTY>' if p.get('name') == '' else p.get('name')
        players.append(
            Player(
                game_guid=test_data.get('guid'),
                slot=p.get('slot'),
                index_player=p.get('index'),
                name=player_name,
                name_hash=md5(player_name.encode('utf-8')).hexdigest(),
                type=p.get('typeEn'),
                team=p.get('team'),
                color_index=p.get('colorIndex'),
                # TODO check if this is always valid
                init_x=p.get('initPosition')[0],
                init_y=p.get('initPosition')[1],
                disconnected=p.get('disconnected'),
                is_winner=p.get('isWinner'),
                is_main_operator=p.get('mainOp'),
                civ_id=p.get('civilization', {}).get('id'),
                civ_name=p.get('civilization', {}).get('nameEn'),
                feudal_time=p.get('feudalTime'),
                castle_time=p.get('castleTime'),
                imperial_time=p.get('imperialTime'),
                resigned_time=p.get('resigned')
            )
        )
    session.add_all(players)

chats = []
if 'chat' in test_data and isinstance(test_data['chat'], list):
    for chat in test_data['chat']:
        chats.append(
            Chat(
                game_guid=test_data.get('guid'),
                recorder_slot=test_data.get('recPlayer'),
                chat_time=chat['time'],
                chat_content=chat['msg']
            )
        )
    session.add_all(chats)

session.add(File(
    game_guid=test_data.get('guid'),
    md5=test_data.get('md5'),
    parser=test_data.get('parser'),
    parse_time=test_data.get('parseTime'),
    parsed_status=test_data.get('status'),
    raw_filename=test_data.get('realfile'),
    raw_lastmodified=test_data.get('lastModified'), # TODO new MgxParser doesn't have this field
    recorder_slot=test_data.get('recPlayer')
))

session.commit()

end_time = time.time()
elapsed_time = end_time - start_time
print(f"\r\nElapsed time: {round(elapsed_time * 1000, 2)} ms")

# close the session
session.close()

# close the engine
engine.dispose()


class DBHandler:
    '''Communicate with the database.'''

    _db_path = None
    _db_engine = None
    _db_session = None

    def __init__(self, db_path: str):
        pass

    def _load_db(self):
        pass

    @property
    def session(self):
        pass

    def get_game(self, game_guid: str | list) -> dict | list:
        pass

    def insert_game(self, game: dict) -> str:
        pass

    def delete_game(self, game_guid: str) -> bool:
        pass

    def stat_index_count(self) -> dict:
        '''Unique games/players count, new games this month.'''
        pass

    def stat_rand_players(self, threshold: int = 10, limit: int = 300) -> list:
        '''Random players.
        
        Including total games of each player. Used mainly in player cloud.

        Args:
            threshold: minimum games of a player to be included.
            limit: maximum number of players to be included.
        '''
        pass

    def stat_last_players(self, limit: int = 300) -> list:
        '''Newly found players.
        
        Including won games, total games, and 1v1 games counts.

        Args:
            limit: maximum number of players to be included.
        '''
        pass

    def stat_close_friends(self, player_name: str, limit: int = 300) -> list:
        '''Players who played with the given player most.'''
        pass

    def filter_games(self, filters: dict, limit: int = 100) -> list:
        '''Filter games by given conditions.'''
        pass

    def update_ratings(self, ratings_dict: dict, batch_size: int = None) -> bool:
        '''Update ratings of players.'''

        if batch_size is None:
            batch_size = len(ratings_dict)

        for i in range(0, len(ratings_dict), batch_size):
            self.session.bulk_insert_mappings(Ratings, ratings_dict[i:i+batch_size])
            self.session.commit()