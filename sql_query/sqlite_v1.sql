-- 首页的统计数据
SELECT 'Unique game_guid count', COUNT(DISTINCT game_guid) AS count FROM games
UNION ALL
SELECT 'Unique player name count', COUNT(DISTINCT name) FROM players
UNION ALL
SELECT 'Games updated last month count', COUNT(*) FROM games WHERE strftime('%m', modified) = strftime('%m', datetime('now', '-1 month')) AND strftime('%Y', modified) = strftime('%Y', 'now');

-- 提取随便机家ID云（含玩家参加过的游戏数量）
SELECT name, game_count FROM (
    SELECT name, COUNT(game_guid) as game_count
    FROM players
    GROUP BY name
    HAVING game_count > 10
) AS player_counts
ORDER BY RANDOM()
LIMIT 300;

-- 查询最新玩家
SELECT 
    ep.name, 
    ep.latest_created, 
    (SELECT COUNT(*) FROM players WHERE name = ep.name AND is_winner = 1) AS win_count,
    (SELECT COUNT(*) FROM players WHERE name = ep.name) AS total_games,
    (SELECT COUNT(*) FROM games g JOIN players p ON g.game_guid = p.game_guid WHERE p.name = ep.name AND g.matchup = '1v1') AS total_1v1_games
FROM 
    (SELECT 
        name,
        MAX(created) AS latest_created
    FROM 
        players
    GROUP BY 
        name
    LIMIT 100) AS ep
ORDER BY 
    ep.latest_created DESC;

-- 查询帝国朋友圈
SELECT 
    p2.name, 
    COUNT(*) AS common_games_count
FROM 
    players p1
JOIN 
    players p2 ON p1.game_guid = p2.game_guid
WHERE 
    p1.name = '_XJL_7_啊菜约局' AND p1.name != p2.name
GROUP BY 
    p2.name
ORDER BY 
    common_games_count DESC
LIMIT 100;