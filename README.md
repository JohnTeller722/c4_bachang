后端版本v0.0.2

已经测试成功的api：

GET /version

GET /ping

POST /user/login

POST /user/logout

GET /user/status

写了还没测试的api：

GET /task/list

POST /task/pause

GET /exp/list

POST /exp/start

POST /exp/stop

POST /exp/config

POST /exp/delete

POST /exp/edit

POST /exp/pause

POST /exp/submit

WEBSOCKET部分

但是具体内容有待填充（等待后续后端文档更新）

其他：

运行：python -m unittest discover -s test以测试
