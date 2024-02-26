'''Used to calculate ELO ratings.'''
from numbers import Number
import math
from statistics import fmean
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import text, and_
from orm_models import Ratings, Player, Game


class EloCalculator:
    '''Elo rating calculator.'''

    _K = 32
    _rating_cache = {}
    _session = None
    _current_game_guid: str | None = None
    _winners_cache = []
    _losers_cache = []

    def __init__(self, session: Session, K: int = 32):
        self._K = K
        self._session = session

    def _calc_rating_delta(self, rating_winner: Number, rating_loser: Number):
        '''Calculate the new Elo rating delta for the winner and loser.

        Args:
            rating_winner: the Elo rating of the winner.
            rating_loser: the Elo rating of the loser.
        '''

        prob_winner = self._calc_probability(rating_winner, rating_loser)
        prob_loser = self._calc_probability(rating_loser, rating_winner)

        return round(self._K * (1 - prob_loser)), round(self._K * (0 - prob_winner))

    def _calc_probability(self, rating_winner: Number, rating_loser: Number):
        '''Calculate the Probability of Winning.'''
        return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating_winner - rating_loser) / 400))

    def _fetch_in_batches(self, query, batch_size: int | None = None):
        '''Fetch the query results in batches.'''
        
        if batch_size is None:
            # If batch_size is None, fetch all results at once
            yield from query.all()
        else:
            # Otherwise, fetch results in batches
            offset = 0
            while True:
                batch = query.limit(batch_size).offset(offset).all()
                if not batch:
                    break
                for row in batch:
                    yield row
                offset += batch_size

    def _update_game_ratings(self, col: dict):
        # Start calculating the ratings for the previous game
        # First check if there are duplicate names in the winners or losers, skip them
        # nh is short for name_hash
        if \
            len([nh for nh, _ in self._winners_cache]) != len(set(nh for nh, _  in self._winners_cache)) \
                or len([nh for nh, _  in self._losers_cache]) != len(set(nh for nh, _  in self._losers_cache)):
            pass
        elif len(self._winners_cache) == 0 or len(self._losers_cache) == 0:
            pass
        else:
            # Calculate average rating of previous game's winners and losers
            rating_winner = fmean([col[nh]["rating"]
                                   for nh, _ in self._winners_cache])
            rating_loser = fmean([col[nh]["rating"]
                                  for nh, _ in self._losers_cache])
            
            # if rating_winner or rating_loser < 1000 or > 3000, print all the ratings of winners and losers
            if rating_winner < 500 or rating_winner > 4000 or rating_loser < 500 or rating_loser > 4000:
                print(f"rating_winner: {rating_winner}, rating_loser: {rating_loser}")
                for nh, _ in self._winners_cache:
                    print(f"winner: {nh}: {col[nh]['rating']}")
                for nh, _ in self._losers_cache:
                    print(f"loser: {nh}: {col[nh]['rating']}")
                exit()

            # Calculate the new Elo rating delta for the winner and loser
            delta_winner, delta_loser = self._calc_rating_delta(
                rating_winner, rating_loser)
            
            # Update the ratings cache
            for _, p in self._winners_cache:
                p["rating"] += delta_winner
                p["total"] += 1
                p["wins"] += 1
                p["highest"] = max(p["rating"], p["highest"])
                p["streak"] += 1
                p["streak_max"] = max(p["streak"], p["streak_max"])

            for _, p in self._losers_cache:
                p["rating"] += delta_loser
                p["total"] += 1
                p["lowest"] = min(p["rating"], p["lowest"])
                p["streak"] = 0

    def _generate_rating_cache(self, duration_threshhold: int = 15 * 60 * 1000, batch_size: int | None = None) -> None:
        '''Generate the ratings cache.'''
        # sql = text(f"""
        #     SELECT players.game_guid,
        #            games.version_code,
        #            games.matchup,
        #            players.name AS name_hash,
        #            players.is_winner,
        #            games.game_time
        #     FROM players
        #     JOIN games ON players.game_guid = games.game_guid
        #     WHERE games.duration > {duration_threshhold} and games.is_multiplayer = 1 and games.include_ai = 0
        #     ORDER BY games.game_time, players.game_guid, players.is_winner
        # """)  # TODO fix name_hash line

        query = self._session.query(
            Player.game_guid,
            Game.version_code,
            Game.matchup,
            Player.name.label('name_hash'),
            Player.is_winner,
            Game.game_time
        ).join(
            Game, Player.game_guid == Game.game_guid
        ).filter(
            and_(Game.duration > duration_threshhold, Game.is_multiplayer == 1, Game.include_ai == 0, Player.is_main_operator == 1)
        ).order_by(
            Game.game_time, Player.game_guid, Player.is_winner
        )

        i = 0
        # Execute the query in batches
        for row in self._fetch_in_batches(query, batch_size):
            game_guid, version_code, matchup, name_hash, is_winner, game_time = row

            if self._current_game_guid is None:
                self._current_game_guid = game_guid
                
            if game_guid != self._current_game_guid:
                # Update the ratings for the previous game
                self._update_game_ratings(col)
                print(f"[{i}] {self._current_game_guid}")
                i += 1

                # Reset the winners and losers for the next game
                self._current_game_guid = game_guid
                self._winners_cache.clear()
                self._losers_cache.clear()

            if version_code not in self._rating_cache:
                self._rating_cache[version_code] = {'1v1': {}, 'team': {}}
            if matchup == '1v1':
                col = self._rating_cache[version_code]['1v1']
            else:
                col = self._rating_cache[version_code]['team']

            # if still the same game, append to winners or losers
            if name_hash not in col:
                col[name_hash] = {
                    "rating": 1600,
                    "total": 0,
                    "wins": 0,
                    "lowest": 1600,
                    "highest": 1600,
                    "streak": 0,
                    "streak_max": 0,
                    "first_played": game_time,
                    "last_played": game_time
                }
            else:
                col[name_hash]["last_played"] = game_time

            # if still same game, append to winners or losers
            if is_winner:
                self._winners_cache.append((name_hash, col[name_hash]))
            else:
                self._losers_cache.append((name_hash, col[name_hash]))

        self._update_game_ratings(col)
        self._current_game_guid = None
        self._winners_cache.clear()
        self._losers_cache.clear()

    def update_ratings(self, duration_threshhold: int = 15 * 60 * 1000, batch_size: int | None = None):
        '''Update the ratings table.'''

        self._generate_rating_cache(duration_threshhold, batch_size)

        # Clear the existing Ratings table
        self._session.query(Ratings).delete()

        # Reset auto increment value (example for MySQL)
        # self._session.execute(text("ALTER TABLE ratings AUTO_INCREMENT = 1"))

        # For SQLite, you can use:
        try:
            self._session.execute(text("UPDATE sqlite_sequence SET seq = 0 WHERE name='ratings'"))
        except OperationalError:
            pass  # Ignore the error if sqlite_sequence table does not exist

        # For PostgreSQL, you can use:
        # self._session.execute(text("ALTER SEQUENCE ratings_id_seq RESTART WITH 1"))

        mappings = []
        for version_code, col in self._rating_cache.items():
            for matchup, players in col.items():
                for name_hash, player in players.items():
                    mappings.append({
                        'version_code': version_code,
                        'matchup': matchup,
                        'name_hash': name_hash,
                        'rating': player["rating"],
                        'wins': player["wins"],
                        'total': player["total"],
                        'streak': player["streak"],
                        'streak_max': player["streak_max"],
                        'highest': player["highest"],
                        'lowest': player["lowest"],
                        'first_played': player["first_played"],
                        'last_played': player["last_played"]
                    })

        self._session.bulk_insert_mappings(Ratings, mappings)

        # Commit the changes
        self._session.commit()

    def set_K(self, K: int):
        '''Set the maximum possible adjustment.'''
        self._K = K

    @property
    def ratings(self):
        '''Return the ratings cache.'''
        return self._rating_cache
