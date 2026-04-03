# Sync Client Python

一个基于Python的文件同步客户端，与sync-server-python后端配合使用。

## 功能特性

- 用户认证（注册/登录）
- 文件同步与冲突解决
- 实时文件监控和同步
- WebSocket支持实时更新
- 自动冲突检测和解决

## 安装

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 通过创建`.env`文件配置客户端（可选）：
```
SERVER_URL=http://localhost:8000
WS_URL=ws://localhost:8000/ws/sync
SYNC_DIR=./sync
```

## 使用方法

### 注册新用户
```bash
python main.py register <用户名> <邮箱> <密码>
```

### 登录
```bash
python main.py login <用户名> <密码>
```

### 开始文件同步
```bash
python main.py sync <用户名> <密码>
```

## 项目结构

```
sync-client-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # 主入口
│   ├── config.py            # 配置管理
│   ├── client.py            # HTTP客户端，用于API调用
│   ├── websocket.py         # WebSocket客户端，用于实时同步
│   ├── watcher.py           # 文件系统监控器
│   ├── sync.py              # 同步管理器
│   ├── models.py            # 数据模型
│   └── utils.py             # 工具函数
├── main.py                  # CLI入口点
├── requirements.txt         # Python依赖
└── README.md               # 本文件
```

## 配置

可以通过环境变量或`.env`文件进行配置：

- `SERVER_URL`: 服务器API地址（默认：http://localhost:8000）
- `WS_URL`: WebSocket地址（默认：ws://localhost:8000/ws/sync）
- `SYNC_DIR`: 本地同步目录（默认：./sync）
- `SYNC_INTERVAL`: 同步间隔（秒）（默认：5）
- `WATCH_INTERVAL`: 文件监控间隔（秒）（默认：1.0）
- `LOG_LEVEL`: 日志级别（默认：INFO）

## API端点

客户端与以下服务器端点通信：

### 认证
- `POST /api/auth/register` - 注册新用户
- `POST /api/auth/login` - 用户登录

### 文件
- `POST /api/files/upload` - 上传文件元数据
- `POST /api/files/upload-content/{file_id}` - 上传文件内容
- `GET /api/files/list` - 列出文件
- `GET /api/files/download/{file_id}` - 下载文件
- `DELETE /api/files/{file_id}` - 删除文件

### 同步
- `POST /api/sync/init` - 初始化同步
- `POST /api/sync/conflict` - 解决冲突
- `GET /api/sync/status` - 获取同步状态

### WebSocket
- `WS /ws/sync?token=xxx` - 实时同步通信

## 冲突解决

当检测到冲突时（相同文件但内容不同），你可以选择：

- `keep_local` - 保留本地版本
- `keep_remote` - 保留远程版本
- `keep_both` - 保留两个版本（创建冲突副本）

## 测试

运行测试套件：

```bash
# 运行所有测试
python run_tests.py

# 或使用unittest
python -m unittest discover tests
```

测试包括：
- 单元测试：工具函数、客户端、同步管理器
- 集成测试：完整的同步流程

## 许可证

MIT License
