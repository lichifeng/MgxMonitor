'''ORM Model of game data'''

from sqlalchemy import Column, Integer, String, \
    DateTime, Boolean, SmallInteger, Text, Index, \
    JSON, DECIMAL, Float, ForeignKey, func, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):  # pylint: disable=missing-class-docstring
    pass


class Game(Base):
    '''Basic game information.

    These information are identical across all players' records.
    '''
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, server_default=func.now(), index=True)
    modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

    game_guid = Column(String(64), unique=True, nullable=False, index=True)
    duration = Column(Integer)
    include_ai = Column(Boolean)
    is_multiplayer = Column(Boolean)
    population = Column(SmallInteger)
    speed = Column(String(20))
    matchup = Column(String(20))
    map_name = Column(String(255))
    map_size = Column(String(20))
    version_code = Column(String(10))
    version_log = Column(SmallInteger)
    version_raw = Column(String(8))
    version_save = Column(DECIMAL(10, 2))
    version_scenario = Column(DECIMAL(10, 2))
    victory_type = Column(String(20))
    source = Column(Text)
    instruction = Column(Text)
    game_time = Column(DateTime)
    first_found = Column(DateTime) # TODO check this

    players = relationship('Player', back_populates='game')
    files = relationship('File', back_populates='game')
    chats = relationship('Chat', back_populates='game')
    legacy_info = relationship('LegacyInfo', back_populates='game')


class Player(Base):
    '''Player information.

    Every player has his own related record file.
    '''
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, server_default=func.now())
    modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

    game_guid = Column(String(64), ForeignKey('games.game_guid'), nullable=False, index=True)
    slot = Column(SmallInteger)
    index_player = Column(SmallInteger)
    name = Column(String(255), index=True, default='<NULL>')
    type = Column(String(20))
    team = Column(SmallInteger)
    color_index = Column(SmallInteger)
    init_x = Column(SmallInteger)
    init_y = Column(SmallInteger)
    disconnected = Column(Boolean)
    is_winner = Column(Boolean)
    is_main_operator = Column(Boolean)
    civ_id = Column(SmallInteger)
    civ_name = Column(String(30))
    feudal_time = Column(Integer)
    castle_time = Column(Integer)
    imperial_time = Column(Integer)
    resigned_time = Column(Integer)

    game = relationship('Game', back_populates='players')
    files = relationship('File', back_populates='recorder', primaryjoin='Player.slot == foreign(File.recorder_slot) and Player.game_guid == File.game_guid')
    chat = relationship('Chat', back_populates='recorder', primaryjoin='Player.slot == foreign(Chat.recorder_slot) and Player.game_guid == Chat.game_guid')

    idx_name_game_guid = Index('idx_name_game_guid', name, game_guid)

class File(Base):
    '''Record file information.

    Every record file has its own related player. Same record file may be 
    uploaded by different people with different file names.
    '''

    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, server_default=func.now())
    modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

    game_guid = Column(String(64), ForeignKey(
        'games.game_guid'), nullable=False)
    md5 = Column(String(32), nullable=False)
    parser = Column(String(50))
    parse_time = Column(Float)
    parsed_status = Column(String(50))
    raw_filename = Column(String(255))
    raw_lastmodified = Column(DateTime) # TODO new MgxParser doesn't have this field
    notes = Column(Text)
    recorder_slot = Column(SmallInteger)

    game = relationship('Game', back_populates='files')
    recorder = relationship('Player', back_populates='files', primaryjoin='foreign(File.recorder_slot) == Player.slot and File.game_guid == Player.game_guid')


class LegacyInfo(Base):
    '''Some legacy information from prior version of mgxhub.'''

    __tablename__ = 'legacy_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime)
    modified = Column(DateTime)
    legacy_id = Column(Integer)
    filenames = Column(JSON)
    game_guid = Column(String(64), ForeignKey(
        'games.game_guid'), nullable=False)

    game = relationship('Game', back_populates='legacy_info')


class Chat(Base):
    '''Chat information.

    One message per record. A game may have multiple messages. 
    Different players may recorded different messages.
    '''

    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, server_default=func.now())
    modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

    game_guid = Column(String(64), ForeignKey(
        'games.game_guid'), nullable=False)
    recorder_slot = Column(SmallInteger)
    chat_time = Column(Integer)
    chat_content = Column(Text)

    game = relationship('Game', back_populates='chats')
    recorder = relationship('Player', back_populates='chat', primaryjoin='foreign(Chat.recorder_slot) == Player.slot and Chat.game_guid == Player.game_guid')


# Create indexes
# Index('idx_game_guid', Game.game_guid)
# Index('idx_name', Player.name)
# Index('idx_created', Game.created)
# Index('idx_player_guid', Player.game_guid)
# Index('idx_name_game_guid', Player.name, Player.game_guid)
