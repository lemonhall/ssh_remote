# SSH远程命令辅助工具 - 设计文档

## 1. 项目概述

这是一个智能SSH远程命令执行助手,通过AI理解用户意图,自动生成并执行远程服务器命令,降低日常运维工作难度。

### 核心功能
- SSH远程连接管理
- 命令历史记录分析
- AI智能命令生成
- 双面板UI(CLI + 聊天界面)
- 命令模板管理
- 安全的凭证处理

## 2. 技术栈

### 后端核心
- **Python 3.11+** (uv项目管理)
- **paramiko** - SSH连接与命令执行
- **OpenAI API** / **Anthropic Claude** - AI对话与命令生成
- **SQLite** - 本地数据存储(命令历史、模板等)

### 前端UI
- **Textual** - 终端UI框架(双面板布局) ✅ 已选定
  - 完美跨平台支持 (Windows/Linux/macOS)
  - 现代化组件、异步支持、响应式布局
- **Rich** - 文本美化与代码高亮辅助

### 配置管理
- **python-dotenv** - 环境变量管理
- **cryptography** - 敏感信息加密存储

## 3. 系统架构

```
┌─────────────────────────────────────────────────┐
│                  用户界面层                      │
│  ┌──────────────┐  ┌────────────────────────┐  │
│  │ SSH CLI面板  │  │   AI聊天面板           │  │
│  │ - 命令输出   │  │   - 对话历史           │  │
│  │ - 实时日志   │  │   - 命令确认           │  │
│  └──────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                  业务逻辑层                      │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐ │
│  │ 会话管理器 │  │ AI服务   │  │ 命令解析器 │ │
│  └────────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                  数据访问层                      │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐ │
│  │ SSH连接池  │  │ 本地数据库│  │ 配置管理   │ │
│  └────────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────┘
```

## 4. 核心模块设计

### 4.1 SSH连接管理 (`ssh_manager.py`)
```python
- SSHConnection: 单个SSH连接封装
- SSHConnectionPool: 连接池管理
- 功能:
  - 连接建立/断开
  - 命令执行(同步/异步)
  - 会话保持
  - 超时处理
```

### 4.2 AI服务 (`ai_service.py`)
```python
- AIAssistant: AI对话管理
- 功能:
  - 上下文理解(基于历史命令)
  - 命令生成
  - 安全检查(危险命令识别)
  - 多轮对话支持
```

### 4.3 命令管理 (`command_manager.py`)
```python
- CommandHistory: 历史命令分析
- CommandTemplate: 命令模板管理
- 功能:
  - history解析与存储
  - 命令模板CRUD
  - 命令分类(nginx、docker、系统等)
  - 常用命令统计
```

### 4.4 会话管理 (`session_manager.py`)
```python
- Session: 单次会话状态
- 功能:
  - 会话上下文维护
  - 多服务器切换
  - 状态持久化
```

### 4.5 UI层 (`ui/`)
```python
- app.py: 主应用入口
- cli_panel.py: SSH CLI面板
- chat_panel.py: AI聊天面板
- 功能:
  - 双面板布局
  - 实时输出更新
  - 命令确认对话框
  - 快捷键支持
```

## 5. 数据模型

### 5.1 服务器配置
```python
Server:
  - id: UUID
  - name: str
  - host: str
  - port: int
  - username: str
  - auth_method: enum(password/key)
  - key_path: Optional[str]
  - created_at: datetime
```

### 5.2 命令历史
```python
CommandRecord:
  - id: UUID
  - server_id: UUID
  - command: str
  - output: str
  - exit_code: int
  - executed_at: datetime
  - source: enum(manual/ai_generated)
```

### 5.3 命令模板
```python
CommandTemplate:
  - id: UUID
  - name: str
  - description: str
  - category: str
  - commands: List[str]  # 多步骤命令
  - created_at: datetime
```

## 6. 安全设计

### 6.1 凭证管理
- **不存储明文密码** - 仅存储SSH密钥路径
- **本地加密** - 使用Fernet对称加密存储敏感配置
- **密钥派生** - 基于机器特征生成加密密钥
- **内存清理** - 及时清理内存中的密码

### 6.2 命令执行安全
- **危险命令检测** - AI识别 `rm -rf`、`dd` 等危险操作
- **确认机制** - 所有AI生成命令需用户确认
- **命令白名单** - 可配置允许的命令模式
- **执行日志** - 完整记录所有执行命令

### 6.3 AI安全
- **API密钥保护** - 通过环境变量加载
- **上下文过滤** - 不将密码等敏感信息发送给AI
- **Prompt注入防护** - 清理用户输入

## 7. 工作流程

### 7.1 基本流程
1. 用户启动应用,选择/添加服务器
2. 建立SSH连接,获取远程history
3. 用户在聊天面板描述需求
4. AI分析历史命令+用户需求,生成命令
5. 展示生成的命令,等待用户确认
6. 执行命令,实时显示输出
7. 保存命令记录和执行结果

### 7.2 命令模板流程
1. 用户执行常用操作(如nginx配置更新)
2. 系统提示保存为模板
3. 命名并分类保存
4. 后续可通过名称快速调用

## 8. 用户界面设计

```
┌─────────────────────────────────────────────────────────┐
│ SSH Remote Assistant [Server: prod-web-01] [●Connected] │
├──────────────────┬──────────────────────────────────────┤
│                  │                                      │
│  SSH Terminal    │  AI Chat Assistant                   │
│                  │                                      │
│  $ ls -la        │  You: 我要重启nginx                  │
│  total 48        │                                      │
│  drwxr-xr-x ...  │  AI: 我理解了,你需要重启nginx服务。  │
│                  │  我会执行以下命令:                   │
│  $ pwd           │                                      │
│  /var/www        │  1. sudo nginx -t                    │
│                  │  2. sudo systemctl restart nginx     │
│                  │                                      │
│                  │  [确认执行] [取消]                   │
│                  │                                      │
│                  │  > _                                 │
├──────────────────┴──────────────────────────────────────┤
│ [F1]Help [F2]Servers [F3]Templates [F10]Quit           │
└─────────────────────────────────────────────────────────┘
```

## 9. 开发计划

### Phase 1: 基础框架 (Week 1-2)
- [x] 项目初始化
- [ ] SSH连接模块
- [ ] 基本UI框架(双面板)
- [ ] 配置管理

### Phase 2: AI集成 (Week 3)
- [ ] AI服务接入
- [ ] 命令生成逻辑
- [ ] 安全检查机制

### Phase 3: 高级功能 (Week 4)
- [ ] 命令历史分析
- [ ] 命令模板系统
- [ ] 会话持久化

### Phase 4: 优化完善 (Week 5+)
- [ ] 错误处理优化
- [ ] 性能优化
- [ ] 文档完善

## 10. 依赖库清单

```toml
[project.dependencies]
# 核心UI (跨平台)
textual = "^0.47.0"          # 终端UI框架
rich = "^13.7.0"             # 文本美化输出

# SSH连接
paramiko = "^3.4.0"          # SSH客户端

# AI服务
openai = "^1.12.0"           # OpenAI API

# 数据与安全
cryptography = "^42.0.0"     # 加密存储
sqlalchemy = "^2.0.0"        # 数据库ORM
pydantic = "^2.6.0"          # 数据验证

# 配置管理
python-dotenv = "^1.0.0"     # 环境变量
```

## 11. 配置文件示例

```bash
# .env (不提交到git)
OPENAI_API_KEY=sk-xxx
ENCRYPTION_KEY_SALT=random-salt-value

# config.toml
[app]
theme = "dark"
log_level = "INFO"

[ssh]
connection_timeout = 30
keepalive_interval = 60

[ai]
model = "gpt-4"
max_context_length = 4000
temperature = 0.7

[security]
dangerous_commands = ["rm -rf", "dd if=", "mkfs", "> /dev/"]
require_confirmation = true
```

---

**注意事项**:
- 本设计文档为初版,实现过程中可根据实际情况调整
- 安全性是首要考虑,所有涉及命令执行的操作都需谨慎处理
- UI体验需要反复打磨,确保信息清晰、操作流畅
