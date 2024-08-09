## 开发约定
- Python一律写类型批注！一律写类型批注！一律写类型批注！
- 剩下的参考PEP8
- 拿不准的交给格式化器ruff

## 用户数据格式约定

用户用flask-security(flask-security-too.readthedocs.io)内置的User-Role模型，添加必要的数据：

用户角色(Role)：
- 临时用户(0)
- 管理员(1)
- 注册用户(2)
---
- 对于不同的安全演练分组，赋予一个Role，号码从100开始。（使用时动态分配）*不优先实现*
- 对于不同的用户小组，赋予一个Role，号码从100000开始。（使用时动态分配）
- 话说Role其实是按名字分配的，但是一定要有一个id。

用户等级：*不优先实现*
- 怎么方便怎么来
- 角色为0,1以及100-99999的用户不显示用户等级。

用户经验：*不优先实现*
- 同上。

用户头像：
- 总之是个jpg图片

包括密码和两步验证之类的安全设定都在flask-login给出了
- 密码用argon2加密(argon2_cffi)

## 数据库

推荐用SQLAlchemy，它把能做的都做了

## 配置

推荐用Dynaconf，但是怎么方便怎么来

## 接口约定

以下接口均以`/api`开始，例如`/login`表示`/api/login`，在Flask中写作`@app.route("/api/login")`

除非另有约定，以下数据一律以json形式给出，以`200 OK`作为返回码。

除非另有约定，消息类都以下列格式返回，MESSAGE用中文：
```json
{
    "status": STATUS_CODE,
    "message": MESSAGE
}
```

以下SOCKET类型接口表示使用socket通信，动态更新数据。

下文中，`消息(STATUS_CODE, MESSAGE)`带入上述模板。

### GET /version

返回后端版本。
例：
```json
{
    "version": "v1.0.0"
}
```

### GET /ping

返回
```json
{
    "status": 200,
    "message": "pong!"
}
```

### POST /user/login

登录接口。

表单数据格式：
```
username:用户名
password:密码 
```

返回数据：
```
登录正确：200,{"status": 200,"message": "OK!"}
凭据错误：401,{"status": 401,"message": "凭据错误，登录失败！请检查你的用户名或密码。"} 
```

### POST /user/logout

登出接口。

成功200，失败400。消息自定。

### GET /user/status

返回用户信息，数据格式见上文。

### GET /exp/list

返回实验列表，数据格式见下文。

### GET /task/list

返回当前运行的实验列表，数据格式见下文。

### POST /exp/start

参数：expUUID=实验UUID号,type=启动类型

例：`/exp/start?expUUID=aaa-bbb-ccc-ddd&type=1`

开启一个实验。

按启动类型分类：
- 为训练模式(1)时，实验允许来自web的VNC或ssh访问，且允许自定义端口映射。该模式不计分。
- 为挑战模式(2)时，实验不允许题目以外的外部访问。
- 若type为0那就是API出错了，返回400 Bad Request

目前不允许同一用户重复启动实验。

启动时细节见下文。

成功200，服务器错误500，请求有误400。

### POST /exp/stop

限制：由自己启动的实验

参数：expUUID=实验UUID号

停止一个实验。实验有关容器全部结束。等待30秒后若仍未结束，则强制结束容器。

成功200，服务器错误500，请求有误400，下同。

### POST /exp/config

权限要求：管理员或对应演练黄方

参数：expUUID=实验UUID号

修改实验range-compose.yml数据。

POST数据：新的range-compose.yml数据，文本base64化

### POST /exp/delete

权限要求：管理员或对应演练黄方

参数：expUUID=实验UUID号

删除该实验。实现时采用软删除（移除到实验回收站）。

### POST /exp/edit

权限要求：管理员或对应演练黄方

参数：expUUID=实验UUID号

修改实验的某项参数。在WebUI，这是一个可视化编辑界面。

### POST /exp/add

权限要求：管理员或对应演练黄方

参数：expUUID=实验UUID号

新建一个实验，同时传入实验配置（可能为空），在此时分配expId与UUID。

### POST /exp/pause

限制：由自己启动的实验

参数：expUUID=实验UUID号

暂停该实验。对应的所有task（任务）被保存退出（*不优先实现*）。

### POST /exp/submit

限制：由自己启动的实验

参数：expUUID=实验UUID号

数据：flag的值，字符串

为实验提交一个flag，以表示实验完成。服务器会校验flag正确性，若正确则在挑战模式下获得对应分数并结束实验。在练习模式下不结束实验但仍会返回flag正确性。

### SOCKET task.ssh

以socket通信，在web上实现ssh。

### SOCKET task.vnc

以socket通信，在web上实现vnc。参考noVNC实现。

### POST /task/pause

暂停某个容器。在挑战模式下不可用。

### SOCKET monitor.resource

返回已启动任务的资源占用。

### SOCKET monitor.traffic

返回已启动任务的网络流量。

### SOCKET monitor.journal

返回容器日志。

以上接口除`/user`外都要做鉴权。

## 实验数据格式约定
```jsonc
{
    "expId": 实验ID，按实验添加顺序递增,
    "expUUID": 实验UUID，随机分配,
    "name": 实验名称,
    "tag":[
        "标签1",
        "标签2",
        "标签3" //各种标签
    ],
    "desc": 实验描述,
    "author": 实验作者,
    "version": 实验版本,
    "status": 实验状态：running--运行中，stopped--已停止，paused--已暂停，not_running--未运行，crashed--已崩溃，failed--（启动）失败，mistaken--配置有误。（建议用数值enum，状态转换图参考附件.jpg）
}
```

## range-compose.yml格式约定
```yaml
version: 1.0 #range-compose格式版本

name: 实验名称
expId: 实验ID，同下，但是是数字。
expUUID: 实验UUID，创建实验的时候yml里没有这行，由服务器分配。是UUID格式的。
tag:
    - 标签1 
    - 标签2
    - 标签3
desc: 实验描述
author: 实验作者
component:
    sample1_container: # 这个是实验子组件名称
        type: container
        config: https://www.example.com/range/Dockerfile # 示例文件
        port: 30001 # 实验对外开放的端口。在服务器，该端口会被用于建立端口映射，例：30001->40310(对外访问)。

    sample2_compose:
        type: compose
        config: https://www.example.com/range/docker-compose.yml

    sample3_k8syml:
        type: kubernetes
        config: apply.yaml #上传时随range-compose.yml一并上传

    sample4_virtmachine:
        type: kubevirt
        config: ubuntu2204_arm_kernel_CVE-2023-32333.yml

    # 注：上面的config都是假的
```

## 关于Socket通信

试试flask-socketio。

一般写作@socket.on("monitor.traffic")

## 运行任务数据约定

```jsonc
{
    "exp": {
        // 此处填对应实验的信息
        "expId": 实验ID,
        "expUUID": 实验UUID,
        "name": 实验名称,
        // 我觉得只放这三个就够了
    },
    "taskID": 任务ID,推荐按UUID随机分配
    "status": 任务状态
}
```
