'''Used to port data from Node.js version of aocrec.com to the Python version. '''

# Connect to localhost MongoDB and MySQL:
#  - MongoDB: database 'mgxhub' and collection 'records', login with username 'root' and password 'example'
#  - MySQL: login with username 'example username' and password 'example password'
# Test their connectbility.

import json
import logging
import time
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from orm_models import Base, Game, Player, File, Chat, LegacyInfo


# Set up logging
logging.basicConfig(filename='./error3.txt',
                    level=logging.ERROR, format='%(asctime)s %(message)s')

# MongoDB connection
mongo_client = MongoClient('mongodb://root:example@172.20.0.3:27017/')
mongo_db = mongo_client['mgxhub']
mongo_collection = mongo_db['records']

# Test MongoDB connection
try:
    # The server_info() command can be used to check if you are connected to MongoDB.
    mongo_client.server_info()
    print("MongoDB connection successful")
except:
    print("Could not connect to MongoDB")


# Function to insert a single document from MongoDB into MySQL
def insert_game_data(doc, session):
    session.add(Game(
        game_guid=doc.get('guid'),
        duration=doc.get('duration'),
        include_ai=doc.get('includeAI'),
        is_multiplayer=doc.get('isMultiplayer'),
        population=doc.get('population'),
        speed=doc.get('speed'),
        matchup=doc.get('teamMode'),
        map_name=doc['map'].get('name') if doc.get('map') else None,
        map_size=doc['map'].get('size') if doc.get('map') else None,
        version_code=doc['version'].get('code') if doc.get('version') else None,
        version_log=doc['version'].get('logVer') if doc.get('version') else None,
        version_raw=doc['version'].get('rawStr') if doc.get('version') else None,
        version_save=doc['version'].get('saveVer') if doc.get('version') else None,
        version_scenario=doc['version'].get('scenarioVersion') if doc.get('version') else None,
        victory_type=doc['victory'].get('type') if doc.get('victory') else None,
        source=doc.get('source'),
        instruction=doc.get('instruction'),
        game_time=doc.get('gameTime'),
        first_found=doc.get('firstFound')
    ))

    # Insert player data
    player_batch = []
    players = doc.get('players')
    if players:
        for player in players:
            player_data = (
                doc.get('guid'),
                player.get('slot'),
                player.get('index'),
                player.get('name'),
                player.get('type'),
                player.get('team'),
                player.get('colorIndex'),
                player.get('initPosition')[0] if player.get('initPosition') else None,
                player.get('initPosition')[1] if player.get('initPosition') else None,
                player.get('disconnected'),
                player.get('isWinner'),
                player.get('mainOp'),
                player.get('civilization').get('id') if player.get('civilization') else None,
                player.get('civilization').get('name') if player.get('civilization') else None,
                player.get('feudalTime'),
                player.get('castleTime'),
                player.get('imperialTime'),
                player.get('resigned')
            )

            player_batch.append(Player(
                game_guid=player_data[0],
                slot=player_data[1],
                index_player=player_data[2],
                name=player_data[3],
                type=player_data[4],
                team=player_data[5],
                color_index=player_data[6],
                init_x=player_data[7],
                init_y=player_data[8],
                disconnected=player_data[9],
                is_winner=player_data[10],
                is_main_operator=player_data[11],
                civ_id=player_data[12],
                civ_name=player_data[13],
                feudal_time=player_data[14],
                castle_time=player_data[15],
                imperial_time=player_data[16],
                resigned_time=player_data[17]
            ))

        session.add_all(player_batch)

    # Insert chat data
    chats_batch = []
    chat_data = doc.get('chat')
    if chat_data:
        for chat_owner, chats in chat_data.items():
            if not chats:
                continue
            for chat in chats:
                chat_owner = int(chat_owner)
                chat_time = int(chat['time']) if 'time' in chat else 0
                chat_content = chat['msg']

                chats_batch.append(
                    Chat(
                        game_guid=doc.get('guid'),
                        recorder_slot=chat_owner,
                        chat_time=chat_time,
                        chat_content=chat_content
                    )
                )
        session.add_all(chats_batch)

    # Insert file data
    files_batch = []
    files = doc.get('files')
    if files:
        for file in files:
            file_data = (
                doc.get('guid'),
                file.get('md5'),
                file.get('recPlayer'),
                file.get('parser'),
                file.get('parseTime'),
                file.get('status'),
                file.get('filename'),
                file.get('uploaded')
            )
            
            files_batch.append(File(
                game_guid=file_data[0],
                md5=file_data[1],
                recorder_slot=file_data[2],
                parser=file_data[3],
                parse_time=file_data[4],
                parsed_status=file_data[5],
                raw_filename=file_data[6],
                raw_lastmodified=file_data[7]
            ))

        session.add_all(files_batch)

    # # Insert legacy info
    # legacy_info = doc.get('legacyInfo')
    # if legacy_info:
    #     legacy_data = (
    #         legacy_info.get('id'),
    #         doc.get('guid'),
    #         legacy_info.get('filenames'),
    #     )


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

# Function to insert data into MySQL


def insert_data_to_sql(collection, max_entries=None):
    start_time = time.time()

    engine = create_engine("sqlite:///test_db3.sqlite3", echo=False)
    Base.metadata.create_all(engine)

    # create a session
    session = Session(engine)

    error_count = 0

    # Iterate over all records in MongoDB
    for i, record in enumerate(collection.find()):
        # If max_entries is set and we've reached the limit, break the loop
        if max_entries is not None and i >= max_entries:
            break
        try:
            insert_game_data(record, session)
            session.commit()
            # Print a hint message with the game guid
            print(f"[{i}] {record['guid']} inserted. Errors: {error_count}. Elapsed: {round(time.time() - start_time, 2)}s")
        except Exception as e:
            session.rollback()
            error_count += 1
            error_message = "An error occurred: " + str(e)
            record_message = JSONEncoder().encode(record)
            logging.error(error_message)
            logging.error(record_message)
            print(f"[error] {i}: {str(record['_id'])}")


    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\r\nElapsed time: {round(elapsed_time * 1000, 2)} ms")

    result = session.execute(text("PRAGMA journal_mode;"))
    print(result.fetchone())


# Call the function to start the data insertion process
# You can now specify the maximum number of entries to process
insert_data_to_sql(mongo_collection, max_entries=None)
