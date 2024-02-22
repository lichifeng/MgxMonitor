
## 功能
这个repo被设计为一个能够独立工作的解析程序和录像仓储数据中心，它能够通过WEB服务器提供一些API（比如即时解析等），同时会启动一个进程监控指定目录下的文件变化，当文件变化时，调用解析器解析文件内容并进行相应的处理。

AOCREC的网站则成为一个前端，通过调用这个库来实现录像的解析和数据的分析展示。

它应该带有一个静态文件服务器，用于提供地图。录像文件被放到单独的OSS服务中。



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

MYSQL_HOST: MySQL数据库地址
MYSQL_PORT: MySQL数据库端口
MYSQL_USER: MySQL数据库用户名
MYSQL_PASSWORD: MySQL数据库密码
MYSQL_DATABASE: MySQL数据库名
