RSFQ xgdx o6o2 i7zt PPzS 8ZK4

## 功能
这个repo被设计为一个能够独立工作的解析程序和录像仓储数据中心，它能够通过WEB服务器提供一些API（比如即时解析等），同时会启动一个进程监控指定目录下的文件变化，当文件变化时，调用解析器解析文件内容并进行相应的处理。

AOCREC的网站则成为一个前端，通过调用这个库来实现录像的解析和数据的分析展示。

它应该带有一个静态文件服务器，用于提供地图。录像文件被放到单独的OSS服务中。

## API
/game/upload: 上传游戏文件   
/game/get/:id: 获取游戏信息   
/game/list: 获取游戏列表 {page, size}
/game/reparse/:id: 重新解析游戏文件   
/game/delete/:id: 删除游戏文件   
/game/update/:id: 更新游戏文件信息 {name, map, duration, players, date, ...}

/rating/list: 获取评分列表 {page, size, version, matchup}   
/rating/get/:id: 获取评分信息   

/stat/summary: 获取统计信息   
/stat/versions: 获取版本统计   
/stat/matchups: 获取对局统计   
/stat/playmost: 获取玩家统计   
/stat/winningrate: 获取胜率统计   
/stat/civs: 获取文明统计   

/player/list: 获取玩家列表 {page, size}   
/player/summary/:id: 获取玩家信息   
/player/games/:id: 获取玩家游戏列表 {page, size}   
/player/friends/:id: 获取玩家好友列表 {page, size}   
/player/rating/:id: 获取玩家评分列表 {page, size}   


## 环境变量
PARSER_PATH: 解析器路径  
MAP_DIR: 存放地图文件文件夹  
WORK_DIR: 工作目录(被监控的目录)   
UPLOAD_DIR: 通过API上传的文件存放目录    
ERROR_DIR: 解析失败的文件存放目录  

S3_ENDPOINT: S3服务地址  
S3_ACCESS_KEY: S3访问密钥  
S3_SECRET_KEY: S3访问密钥  
S3_BUCKET: S3存储桶   

SQLITE_PATH: SQLite数据库文件路径
RATING_DURATION_THRESHOLD: 评分持续时间阈值    
RATING_CALC_BATCH_SIZE: 评分计算批处理大小    
RATING_CALC_LOCK_FILE: 评分计算锁文件   

## miniconda
```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash Miniconda3-latest-Linux-x86_64.sh -b
~/miniconda3/bin/conda init
conda env create --file environment.yml
conda activate mgxhub-deploy
```