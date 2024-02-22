CREATE TABLE IF NOT EXISTS games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    game_guid VARCHAR(64) NOT NULL UNIQUE,
    duration INT UNSIGNED,
    include_ai TINYINT(1),
    is_multiplayer TINYINT(1),
    population SMALLINT UNSIGNED,
    speed VARCHAR(20),
    matchup VARCHAR(20),
    map_name VARCHAR(255),
    map_size VARCHAR(20),
    version_code VARCHAR(10),
    version_log TINYINT UNSIGNED,
    version_raw VARCHAR(8),
    version_save DECIMAL(10,2),
    version_scenario DECIMAL(10,2),
    victory_type VARCHAR(20),
    source TEXT,
    instruction TEXT,
    game_time DATETIME,
    first_found DATETIME,
    last_updated DATETIME
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS players (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    game_guid VARCHAR(64) NOT NULL,
    slot TINYINT,
    index_player TINYINT,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20),
    team TINYINT,
    color_index TINYINT UNSIGNED,
    init_x SMALLINT,
    init_y SMALLINT,
    disconnected TINYINT(0),
    is_winner TINYINT(0),
    is_main_operator TINYINT(1),
    civ_id SMALLINT,
    civ_name VARCHAR(30),
    feudal_time INT UNSIGNED,
    castle_time INT UNSIGNED,
    imperial_time INT UNSIGNED,
    resigned_time INT UNSIGNED,
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    game_guid VARCHAR(64) NOT NULL,
    md5 CHAR(32) NOT NULL,
    recorder TINYINT,
    parser VARCHAR(50),
    parse_time FLOAT,
    parsed_status VARCHAR(50),
    raw_filename VARCHAR(255),
    raw_lastmodified DATETIME,
    notes TEXT,
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS legacy_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    legacy_id INT UNSIGNED,
    filenames JSON,
    game_guid VARCHAR(64),
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    game_guid VARCHAR(64) NOT NULL,
    recorder TINYINT,
    chat_time INT UNSIGNED,
    chat_content TEXT,
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX idx_game_guid ON games(game_guid);
CREATE INDEX idx_name ON players(name);
CREATE INDEX idx_created ON games(created);
CREATE INDEX idx_players_guid ON players(game_guid);
CREATE INDEX idx_name_game_guid ON players(name, game_guid);