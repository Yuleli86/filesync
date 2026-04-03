# 文件同步服务端 API (Python版本)

基于 Python + FastAPI + SQLAlchemy 的文件同步服务端 API，支持实时同步、双向同步、增量传输、冲突解决等功能。

## 技术栈

- **框架**：FastAPI (高性能异步Web框架)
- **数据库**：SQLAlchemy + SQLite (开发) / PostgreSQL (生产)
- **认证**：JWT (PyJWT)
- **WebSocket**：原生支持 (用于实时同步)
- **异步支持**：asyncio + async/await
- **数据验证**：Pydantic
- **文件操作**：aiofiles (异步文件操作)

## 功能特性

- ✅ **用户认证**：注册、登录，基于JWT认证
- ✅ **文件管理**：上传、下载、列出、删除文件
- ✅ **实时同步**：基于WebSocket的实时同步
- ✅ **双向同步**：支持双向文件同步
- ✅ **增量传输**：只传输变化的文件
- ✅ **冲突解决**：提供多种冲突解决策略
- ✅ **多用户支持**：支持多用户同时使用
- ✅ **权限控制**：基于角色的权限管理
- ✅ **自动API文档**：自动生成Swagger文档

## 目录结构

```
sync-server-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py          # 用户模型
│   │   ├── file.py          # 文件模型
│   │   └── sync.py          # 同步模型
│   ├── routers/             # API路由
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证路由
│   │   ├── files.py         # 文件路由
│   │   └── sync.py          # 同步路由
│   ├── websocket/           # WebSocket处理
│   │   ├── __init__.py
│   │   └── handler.py       # WebSocket处理器
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── security.py      # 安全工具
├── uploads/                 # 文件存储目录
├── tests/                   # 测试文件
├── requirements.txt         # 依赖管理
├── .env.example            # 环境变量示例
├── run.py                  # 启动脚本
└── README.md               # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置相应的配置
```

### 3. 运行服务器

```bash
# 使用启动脚本
python run.py

# 或者使用uvicorn直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

启动服务器后，访问以下地址查看自动生成的API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 接口

### 认证接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### 文件接口

- `POST /api/files/upload` - 上传文件元数据
- `POST /api/files/upload-content/{file_id}` - 上传文件内容
- `GET /api/files/list` - 列出文件
- `GET /api/files/download/{file_id}` - 下载文件
- `DELETE /api/files/{file_id}` - 删除文件

### 同步接口

- `POST /api/sync/init` - 初始化同步
- `POST /api/sync/conflict` - 处理冲突
- `GET /api/sync/status` - 获取同步状态

### WebSocket 接口

- `WS /ws/sync?token={jwt_token}` - 实时同步连接

### 其他接口

- `GET /` - 根路径
- `GET /health` - 健康检查

## WebSocket 消息类型

### 客户端发送

- `PING` - 心跳检测
- `SYNC_REQUEST` - 同步请求
- `FILE_CHANGED` - 文件变化通知
- `CONFLICT_RESOLUTION` - 冲突解决

### 服务器响应

- `PONG` - 心跳响应
- `CONNECTED` - 连接成功
- `SYNC_RESPONSE` - 同步响应
- `SYNC_PROGRESS` - 同步进度
- `SYNC_COMPLETED` - 同步完成
- `FILE_CHANGED_ACK` - 文件变化确认
- `FILE_CHANGED_NOTIFICATION` - 文件变化通知
- `CONFLICT_RESOLUTION_ACK` - 冲突解决确认
- `ERROR` - 错误信息

## 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| HOST | 服务器主机 | 0.0.0.0 |
| PORT | 服务器端口 | 8000 |
| DATABASE_URL | 数据库连接URL | sqlite+aiosqlite:///./sync_server.db |
| SECRET_KEY | JWT密钥 | your-secret-key-here |
| ALGORITHM | JWT算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token过期时间(分钟) | 30 |
| UPLOAD_DIR | 上传目录 | ./uploads |
| MAX_FILE_SIZE | 最大文件大小(字节) | 104857600 (100MB) |
| CHUNK_SIZE | 文件传输块大小(字节) | 8192 (8KB) |
| SYNC_INTERVAL | 同步间隔(秒) | 5 |
| ENCRYPTION_KEY | 加密密钥 | your-encryption-key-here |

## 使用示例

### 用户注册

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword"
  }'
```

### 用户登录

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpassword"
```

### 上传文件元数据

```bash
curl -X POST "http://localhost:8000/api/files/upload" \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/documents",
    "filename": "test.txt",
    "size": 1024,
    "file_hash": "abc123...",
    "last_modified": "2024-01-01T00:00:00",
    "is_directory": false
  }'
```

### WebSocket连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/sync?token=your_jwt_token');

ws.onopen = function() {
  console.log('Connected');
  ws.send(JSON.stringify({type: 'PING'}));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 部署建议

### 开发环境
- 使用SQLite数据库
- 启用热重载 (`--reload`)
- 日志级别设置为 `info`

### 生产环境
- 使用PostgreSQL数据库
- 禁用热重载
- 配置HTTPS
- 使用Gunicorn + Uvicorn工作进程
- 配置反向代理 (Nginx)
- 日志级别设置为 `warning`

```bash
# 生产环境启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 注意事项

1. **安全性**：生产环境请使用强密码和安全的密钥
2. **文件存储**：确保上传目录有适当的权限
3. **数据库**：生产环境建议使用PostgreSQL
4. **HTTPS**：生产环境必须启用HTTPS
5. **备份**：定期备份数据库和上传的文件

## 许可证

MIT License
