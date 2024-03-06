import unittest
from mgxhub.handler import DBHandler
from mgxhub.config import Config
from unittest.mock import MagicMock

class TestDBHandler(unittest.TestCase):
    def setUp(self):
        Config().load('testconf.ini')
        self.db_handler = DBHandler()

    def test_stat_index_count(self):
        stats = self.db_handler.fetch_index_stats()
        print(stats)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('unique_games', stats)
        self.assertIn('unique_players', stats)
        self.assertIn('monthly_games', stats)
        self.assertGreater(stats['unique_games'], 0)
        self.assertGreater(stats['unique_players'], 0)

    def test_stat_rand_players(self):
        stats = self.db_handler.fetch_rand_players(10, 100)
        print(stats)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('players', stats)

    def test_stat_latest_players(self):
        stats = self.db_handler.fetch_latest_players(20)
        print(stats)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('players', stats)

    def test_stat_close_friends(self):
        stats = self.db_handler.fetch_close_friends('_XJL_6.25平静', 100)
        print(stats)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('players', stats)

if __name__ == '__main__':
    unittest.main()