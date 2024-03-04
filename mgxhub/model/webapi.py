'''Some models used in the API.'''

import gettext
from datetime import datetime
from pydantic import BaseModel
from mgxhub.model.orm import Game, Player, File, Chat


class RecordFile(BaseModel):
    '''Record file information.'''

    game_guid: str | None  # If used in GameDetail, this field is not required
    md5: str
    parser: str
    parse_time: float
    parsed_status: str
    recorder_slot: int
    raw_filename: str
    raw_lastmodified: datetime | None
    source: str | None
    notes: str | None


class PlayerInGame(BaseModel):
    '''Detail information of a player in a game.'''

    slot: int | None  # If used in GameDetail, this field is put at the place of dict key
    index: int
    name: str
    name_hash: str
    type: str
    team: int
    color_index: int
    init_x: float
    init_y: float
    disconnected: bool
    is_winner: bool
    is_main_operator: bool
    civ_id: int
    civ_name: str
    feudal_time: int | None
    castle_time: int | None
    imperial_time: int | None
    resigned_time: int | None
    files: list[RecordFile] | None


class ChatEntry(BaseModel):
    '''Chat entry in a game.

    Chat records in lobby have `sent_time` value of 0.

    - **sent_time**: In-game time when the chat was sent. Avoid using `time` as field name.
    - **content**: Content of the chat.
    '''

    sent_time: int
    content: str


class GameDetail(BaseModel):
    '''Basic information of a game.'''

    guid: str
    game_time: datetime | None
    version_code: str | None
    version_log: int | None
    version_raw: str | None
    version_save: float | None
    version_scenario: float | None
    victory_type: str | None
    instruction: str | None
    speed: str | None
    map_name: str | None
    map_size: str | None
    matchup: str | None
    population: int | None
    include_ai: bool | None
    is_multiplayer: bool | None
    duration: int | None
    players: dict[int, PlayerInGame] | None
    chats: list[ChatEntry] | None

    def __init__(self, g: Game, p: list[Player], f: list[File], c: list[Chat], lang: str = 'en'):
        '''Load data from ORM models.

        Args:
            g: Game information.
            p: Player information.
            f: File information.
            c: Chat information.
            lang: Language code. Default is 'en'.

        Returns:
            GameDetail: Return the instance itself with data loaded.
        '''

        # if translations/en/LC_MESSAGES/<lang>.mo exists, use it
        # print(gettext.find(lang, 'translations', languages=["en"], all=True))
        t = gettext.translation(lang, localedir='translations', languages=["en"], fallback=True)
        _ = t.gettext

        super().__init__(
            guid=g.game_guid,
            game_time=g.game_time,
            version_code=g.version_code,
            version_log=g.version_log,
            version_raw=g.version_raw,
            version_save=g.version_save,
            version_scenario=g.version_scenario,
            victory_type=_(g.victory_type),
            instruction=g.instruction,
            speed=_(g.speed),
            map_name=_(g.map_name),
            map_size=_(g.map_size),
            matchup=g.matchup,
            population=g.population,
            include_ai=g.include_ai,
            is_multiplayer=g.is_multiplayer,
            duration=g.duration,
            players={},
            chats=[]
        )

        for player in p:
            if player.slot not in self.players:
                self.players[player.slot] = PlayerInGame(
                    slot=player.slot,
                    index=player.index_player,
                    name=player.name,
                    name_hash=player.name_hash,
                    type=_(player.type),
                    team=player.team,
                    color_index=player.color_index,
                    init_x=player.init_x,
                    init_y=player.init_y,
                    disconnected=player.disconnected,
                    is_winner=player.is_winner,
                    is_main_operator=player.is_main_operator,
                    civ_id=player.civ_id,
                    civ_name=_(player.civ_name),
                    feudal_time=player.feudal_time,
                    castle_time=player.castle_time,
                    imperial_time=player.imperial_time,
                    resigned_time=player.resigned_time,
                    files=[]
                )

        for file in f:
            if file.recorder_slot in self.players:
                self.players[file.recorder_slot].files.append(RecordFile(
                    game_guid=file.game_guid,
                    md5=file.md5,
                    parser=file.parser,
                    parse_time=file.parse_time,
                    parsed_status=file.parsed_status,
                    recorder_slot=file.recorder_slot,
                    raw_filename=file.raw_filename,
                    raw_lastmodified=file.raw_lastmodified,
                    source=file.source,
                    notes=file.notes
                ))

        self.chats = [ChatEntry(
            sent_time=chat.chat_time, content=chat.chat_content) for chat in c]
