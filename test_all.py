import os
import time
import uuid
from shutil import copyfile
from time import sleep
import asyncio
import unittest
import record_parser as rp
from s3_adapter import S3Adapter
from file_handler import FileHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from elo_calc import EloCalculator
from orm_models import Ratings, Base

s3_test = [
    "play.min.io",
    "Q3AM3UQ867SPQQA43P2F",
    "zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    "aocrec-test-bucket"
]


# Test file_handler.py
class TestFileHandler(unittest.IsolatedAsyncioTestCase):
    def test_handle_record_sync(self):
        start_time = time.time()

        test_obj1 = '/records/7ce24dd2608dec17d85d48c781853997.zip'
        test_obj2 = '/records/717cd3fc274a200ba81a2cc2cc65c288.zip'
        ossconn = S3Adapter(*s3_test)
        ossconn.remove_object(test_obj1)
        ossconn.remove_object(test_obj2)

        copyfile('test/recs_in_zip.zip', 'test/recs_in_zip_tmp.zip')

        hd = FileHandler('test/recs_in_zip_tmp.zip', s3_test, False, "", True)
        result = hd.process()
        self.assertEqual(result['status'], 'success')
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\r\nElapsed time: {elapsed_time} seconds")

        self.assertTrue(ossconn.have('/records/7ce24dd2608dec17d85d48c781853997.zip'))
        self.assertTrue(ossconn.have('/records/717cd3fc274a200ba81a2cc2cc65c288.zip'))

    def test_handle_record_async(self):
        start_time = time.time()

        test_obj1 = '/records/5e3b2a7e604f71c8a3793d41f522639c.zip'
        ossconn = S3Adapter(*s3_test)
        ossconn.remove_object(test_obj1)
        self.assertFalse(ossconn.have('/records/5e3b2a7e604f71c8a3793d41f522639c.zip'))

        copyfile('test/test_record1.mgx', 'test/test_record1_tmp.mgx')

        hd = FileHandler('test/test_record1_tmp.mgx', s3_test, False, "./", True)
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
        with open('test/sample_base64_map.txt', 'r') as f:
            base64_str = f.read()
            hd = FileHandler(
                'test/test_record1.mgx',
                s3_creds=s3_test,
                map_dir='./'
            )
            result = asyncio.run(hd._save_map('testmap', base64_str))
            self.assertEqual(result, 'MAP_SAVE_SUCCESS')
            self.assertTrue(os.path.isfile("testmap.png"))
            os.remove("testmap.png")


# Test record_parser.py
class TestRecordParser(unittest.TestCase):
    def test_parse(self):
        result = rp.parse('test/test_record1.mgx')
        self.assertEqual(result['status'], 'perfect')


# Test s3_uploader.py
class TestS3Uploader(unittest.TestCase):
    def test_upload(self):
        random_uuid = uuid.uuid4()
        random_filename = str(random_uuid) + '.dat'

        ossconn = S3Adapter(*s3_test)

        result = ossconn.upload(
            'test/test_record1.mgx',
            random_filename
        )
        self.assertEqual(result.etag, "5e3b2a7e604f71c8a3793d41f522639c")

        result = ossconn.have(random_filename)
        self.assertTrue(result)

        result = ossconn.have(random_filename + 'notexist')
        self.assertFalse(result)

# Test elo_calc.py
class TestEloCalculator(unittest.TestCase):
    def setUp(self):
        # Create a new EloCalculator for each test
        engine = create_engine('sqlite:///test_db2.sqlite3')
        # Create all tables
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        self.calculator = EloCalculator(session)

    def test_update_ratings(self):
        # Test that update_ratings works correctly
        start_time = time.time()
        self.calculator.update_ratings(batch_size=500000)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\r\nCalculation time: {elapsed_time} seconds")

        top_10 = self.calculator._session.query(Ratings).filter(
            Ratings.version_code == 'AOC10',
            Ratings.matchup == 'team'
        ).order_by(
            Ratings.rating.desc()
        ).limit(20).all()
        print(f"\r\nTop 20 team ratings for AOC10 team games:")
        for row in top_10:
            print(f"[{row.id}] {row.name_hash}: {row.rating} wins: {row.wins} total: {row.total} highest: {row.highest} lowest: {row.lowest} streak: {row.streak}/{row.streak_max} first_played: {row.first_played} last_played: {row.last_played}")


if __name__ == '__main__':
    unittest.main()
