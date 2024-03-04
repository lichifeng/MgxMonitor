'''Tests'''

import os
import time
import uuid
from shutil import copyfile
from time import sleep
import asyncio
import unittest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mgxhub.rating import EloCalculator
from mgxhub.model.orm import Rating, Base
from mgxhub.parser import parse
from mgxhub.handler import FileHandler
from mgxhub.storage import S3Adapter
from mgxhub.handler import DBHandler
from mgxhub.config import cfg


class TestFileHandler(unittest.IsolatedAsyncioTestCase):
    '''Test FileHandler class.
    Path: mgxhub/handler/file_handler.py
    '''

    def test_handle_record_sync(self):
        '''Test file uploading process.'''

        start_time = time.time()

        test_obj1 = '/records/7ce24dd2608dec17d85d48c781853997.zip'
        test_obj2 = '/records/717cd3fc274a200ba81a2cc2cc65c288.zip'
        ossconn = S3Adapter(**cfg.s3)
        ossconn.remove_object(test_obj1)
        ossconn.remove_object(test_obj2)

        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        f1 = os.path.join(script_dir, 'samples/recs_in_zip.zip')
        f2 = os.path.join(script_dir, 'samples/recs_in_zip_tmp.zip')
        copyfile(f1, f2)

        hd = FileHandler(f2, False, True, DBHandler())
        result = hd.process()
        self.assertEqual(result['status'], 'success')
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\r\nElapsed time: {elapsed_time} seconds")

        self.assertTrue(ossconn.have('/records/7ce24dd2608dec17d85d48c781853997.zip'))
        self.assertTrue(ossconn.have('/records/717cd3fc274a200ba81a2cc2cc65c288.zip'))

    def test_handle_record_async(self):
        '''Test file uploading process with async.'''

        start_time = time.time()

        test_obj1 = '/records/5e3b2a7e604f71c8a3793d41f522639c.zip'
        ossconn = S3Adapter(**cfg.s3)
        ossconn.remove_object(test_obj1)
        self.assertFalse(ossconn.have('/records/5e3b2a7e604f71c8a3793d41f522639c.zip'))

        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        f1 = os.path.join(script_dir, 'samples/test_record1.mgx')
        f2 = os.path.join(script_dir, 'samples/test_record1_tmp.mgx')
        copyfile(f1, f2)

        hd = FileHandler(f2, False, True)
        if os.path.isfile('./d46a6ae13bea04e1744043f5017f9786.png'):
            os.remove('./d46a6ae13bea04e1744043f5017f9786.png')
        result = hd.process()
        self.assertEqual(result['status'], 'perfect')

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\r\nElapsed time: {elapsed_time} seconds")

        self.assertFalse(ossconn.have('/records/5e3b2a7e604f71c8a3793d41f522639c.zip'))
        for _ in range(10):
            if ossconn.have('/records/5e3b2a7e604f71c8a3793d41f522639c.zip') and os.path.isfile('./d46a6ae13bea04e1744043f5017f9786.png'):
                break
            sleep(1)
        self.assertTrue(ossconn.have('/records/5e3b2a7e604f71c8a3793d41f522639c.zip'))
        hd._clean_file('./d46a6ae13bea04e1744043f5017f9786.png')

    def test_save_map(self):
        '''Test saving map.'''

        with open('test/samples/base64_map.txt', 'r') as f:
            base64_str = f.read()
            hd = FileHandler(
                'test/test_record1.mgx'
            )
            result = asyncio.run(hd._save_map('testmap', base64_str))
            self.assertEqual(result, 'MAP_SAVE_SUCCESS')
            map_path = os.path.join(cfg.get('system', 'mapdir'), "testmap.png")
            self.assertTrue(os.path.isfile(map_path))
            os.remove(map_path)


class TestRecordParser(unittest.TestCase):
    '''Test record parser.'''

    def test_parse(self):
        '''Test parsing a record.'''

        result = parse('test/samples/test_record1.mgx')
        self.assertEqual(result['status'], 'perfect')


class TestS3Uploader(unittest.TestCase):
    '''Test S3Adapter class.'''

    def test_upload(self):
        random_uuid = uuid.uuid4()
        random_filename = str(random_uuid) + '.dat'

        ossconn = S3Adapter(**cfg.s3)

        result = ossconn.upload(
            'test/samples/test_record1.mgx',
            random_filename
        )
        self.assertEqual(result.etag, "5e3b2a7e604f71c8a3793d41f522639c")

        result = ossconn.have(random_filename)
        self.assertTrue(result)

        result = ossconn.have(random_filename + 'notexist')
        self.assertFalse(result)


class TestEloCalculator(unittest.TestCase):
    '''Test EloCalculator class.'''

    def setUp(self):
        # Create a new EloCalculator for each test
        engine = create_engine('sqlite:///test_db.sqlite3')
        # Create all tables
        Base.metadata.create_all(engine)
        _session = sessionmaker(bind=engine)
        session = _session()
        self.calculator = EloCalculator(session)

    def test_update_ratings(self):
        # Test that update_ratings works correctly

        start_time = time.time()
        self.calculator.update_ratings(batch_size=1000000)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\r\nCalculation time: {elapsed_time} seconds")

        top_10 = self.calculator._session.query(Rating).filter(
            Rating.version_code == 'AOC10',
            Rating.matchup == 'team'
        ).order_by(
            Rating.rating.desc()
        ).limit(20).all()
        print(f"\r\nTop 20 team ratings for AOC10 team games:")
        for row in top_10:
            print(f"[{row.id}] {row.name_hash}: {row.rating} wins: {row.wins} total: {row.total} highest: {row.highest} lowest: {
                  row.lowest} streak: {row.streak}/{row.streak_max} first_played: {row.first_played} last_played: {row.last_played}")


class TestRecordCRUD(unittest.TestCase):
    '''Test record CRUD operations.'''

    def test_crud(self):
        '''Test record CRUD operations.'''

        testdb = os.path.join(cfg.get('system', 'workdir'), 'test_db_crud.sqlite3')
        try:
            os.remove(testdb)
        except FileNotFoundError:
            pass
        dbh = DBHandler(testdb)

        # INSERTATION
        # load test/samples/parsed_data_zip.json and parsed the json string into
        # a dict as test data
        script_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(script_dir, 'samples', 'parsed_data.json')

        with open(file_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            result = dbh.add_game(data)
            print(f"\r\nGuid of test game: {data["guid"]}")
            self.assertEqual(result[0], 'success')
            print(f"Game inserted, guid: {result[1]}")
            data["duration"] += 1
            result = dbh.add_game(data)
            self.assertEqual(result[0], 'updated')
            print(f"Game updated, guid: {result[1]}")
            data["duration"] -= 1
            result = dbh.add_game(data)
            self.assertEqual(result[0], 'exists')
            print(f"Game exists, guid: {result[1]}")

        # RETRIEVAL
        # retrieve the game from the database
        game = dbh.get_game(data["guid"])
        self.assertEqual(game.guid, data["guid"])
        print(f"Game retrieved, guid: {game.guid}")

        # DELETION
        # delete the game and related chats, players, legacy_info, etc.
        result = dbh.delete_game(data["guid"])
        self.assertEqual(result, True)
        game = dbh.get_game(data["guid"])
        self.assertEqual(game, None)
        print(f"Game deleted, guid: {data["guid"]}")


if __name__ == '__main__':
    unittest.main()
