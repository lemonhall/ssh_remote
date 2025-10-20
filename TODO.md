# SSH Remote Assistant - 项目架构总览

## ✅ 已完成

### 1. 项目初始化
- [x] uv 项目配置
- [x] 依赖管理 (pyproject.toml)
- [x] 目录结构搭建

### 2. 核心模块

#### 配置管理 (`config.py`)
- [x] Settings 配置类
- [x] 环境变量读取
- [x] 危险命令列表
- [x] 数据目录初始化

#### 数据模型 (`models/`)
- [x] Server - 服务器配置
- [x] CommandRecord - 命令记录
- [x] CommandTemplate - 命令模板
- [x] ChatMessage - 聊天消息
- [x] AuthMethod / CommandSource 枚举

#### SSH管理 (`core/ssh_manager.py`)
- [x] SSHConnection 类
- [x] 连接建立/断开
- [x] 交互式Shell支持
- [x] 连接状态管理

#### AI服务 (`services/ai_service.py`)
- [x] AIAssistant 类
- [x] OpenAI API 集成
- [x] 命令生成逻辑
- [x] 危险命令检测
- [x] 对话历史管理
- [x] 命令解析

## 🔄 重构中 (2025-10-21)

### UI框架迁移：Textual → prompt_toolkit + pyte

**原因**：Textual不支持真正的终端仿真，无法运行vim/nano等全屏应用

#### 新UI架构 (`ui/terminal_app.py`) - 阶段性完成
- [x] 抛弃Textual框架
- [x] 引入prompt_toolkit (专业TUI框架)
- [x] 引入pyte (完整终端模拟器)
- [x] SSHTerminalSession - SSH会话+终端仿真
- [x] 基础双面板布局
- [x] SSH连接成功，可显示终端提示符
- [x] ANSI颜色支持（使用ANSI格式化）
- [x] 键盘事件绑定（字母、数字、符号、特殊键、Ctrl组合键）
- [x] 焦点切换机制（Ctrl+T）
- [x] 状态栏显示
- [⚠️] **终端输入处理 - 有问题需重构**
  - 键绑定已实现，但焦点管理与prompt_toolkit冲突
  - `layout.focus(None)` 报错，无法正确实现"无焦点"状态
  - 需要重新设计焦点管理方案

### � 当前问题 (2025-10-21 晚)

#### 焦点管理问题
**症状**：
- SSH终端可以显示提示符和输出
- 但无法接收键盘输入
- 尝试用 `layout.focus(None)` 实现"无焦点"模式失败
- 错误：`ValueError: Not a container object: None`

**根本原因**：
- prompt_toolkit要求始终有一个Widget获得焦点
- TextArea组件会捕获所有输入，干扰自定义键绑定
- 使用Filter条件无法完全阻止TextArea接收输入
- 当前的"双焦点"设计（终端模式 vs 聊天模式）与框架机制冲突

**需要的解决方案**：
1. **方案A**: 创建一个虚拟的隐藏Widget作为终端模式的焦点目标
2. **方案B**: 完全重构，使用自定义的Window而非TextArea
3. **方案C**: 放弃双面板交互，改为模态切换（要么全屏终端，要么全屏聊天）
4. **方案D**: 研究prompt_toolkit的input_processors自定义输入处理

## 📋 下一步计划

### 🎯 优先级1: 修复终端输入（需重新设计）
- [ ] 重新评估UI架构方案
- [ ] 解决焦点管理问题
- [ ] 实现可用的终端输入
  
### 优先级2: 基础功能完善
- [ ] 终端大小自适应
- [ ] 实时输出刷新优化
  
### 优先级3: AI聊天集成
- [ ] 右侧输入框功能
- [ ] AI命令生成
- [ ] 命令发送到左侧终端执行

### Phase 2: 核心功能增强
- [ ] 命令确认机制
  - [ ] 危险命令检测弹窗
  - [ ] 命令预览和确认
  
- [ ] 多服务器管理
  - [ ] 服务器列表界面
  - [ ] 快速切换连接

### Phase 2: 数据持久化
- [ ] 数据库模块 (`core/database.py`)
  - [ ] SQLAlchemy 表定义
  - [ ] CRUD 操作
  
- [ ] 服务器配置存储
  - [ ] 保存/加载服务器信息
  - [ ] SSH密钥路径管理
  
- [ ] 命令历史记录
  - [ ] 本地历史保存
  - [ ] 远程history同步
  - [ ] 历史命令搜索

### Phase 3: 高级功能
- [ ] 命令模板系统
  - [ ] 模板创建界面
  - [ ] 模板分类管理
  - [ ] 模板快速调用
  
- [ ] 会话管理
  - [ ] 多服务器切换
  - [ ] 会话状态保存
  - [ ] 会话恢复
  
- [ ] 安全增强
  - [ ] 密码加密存储
  - [ ] 命令白名单
  - [ ] 操作审计日志

### Phase 4: 体验优化
- [ ] UI增强
  - [ ] 命令语法高亮
  - [ ] 快捷键优化
  - [ ] 主题切换
  - [ ] 响应式优化
  
- [ ] 错误处理
  - [ ] 友好的错误提示
  - [ ] 网络断开重连
  - [ ] 异常恢复机制
  
- [ ] 性能优化
  - [ ] 异步命令执行
  - [ ] 输出流式显示
  - [ ] 内存优化

## 📦 当前文件结构

```
ssh_remote/
├── ssh_remote/
│   ├── __init__.py          ✅ 包初始化
│   ├── main.py              ✅ 程序入口
│   ├── config.py            ✅ 配置管理
│   ├── core/
│   │   ├── __init__.py      ✅
│   │   └── ssh_manager.py   ✅ SSH连接管理 (已支持交互式Shell)
│   ├── services/
│   │   ├── __init__.py      ✅
│   │   └── ai_service.py    ✅ AI命令生成
│   ├── models/
│   │   └── __init__.py      ✅ 数据模型
│   └── ui/
│       ├── __init__.py      ✅
│       ├── app.py           ❌ 已废弃 (Textual)
│       └── terminal_app.py  🔄 新UI (prompt_toolkit + pyte)
├── pyproject.toml           ✅ 项目配置 (已更新依赖)
├── server_config.json       ✅ 服务器配置
├── README.md                ✅ 项目说明
├── DESIGN.md                ✅ 设计文档
├── .env.example             ✅ 环境变量示例
└── TODO.md                  ✅ 任务清单 (本文件)
```

## 🚀 快速测试

```powershell
# 1. 安装依赖
uv sync

# 2. 配置服务器信息
# 编辑 server_config.json，填入你的服务器信息

# 3. (可选) 配置AI
# 编辑 .env 填入你的 OPENAI_API_KEY

# 4. 运行应用
uv run python -m ssh_remote.main
```

## 🎯 技术栈变更

**旧方案（已废弃）：**
- ❌ Textual - TUI框架（不支持完整终端仿真）
- ❌ Rich - 文本渲染

**新方案（当前）：**
- ✅ prompt_toolkit - 专业TUI框架
- ✅ pyte - 完整VT100终端模拟器
- ✅ 支持 vim/nano/top/htop 等全屏应用

## 📝 重构记录

**2025-10-21 上午**: 
- 移除 Textual 框架依赖
- 引入 prompt_toolkit + pyte
- 创建 SSHTerminalSession 类（SSH + 终端仿真）
- 实现基础双面板布局

**2025-10-21 晚上**:
- ✅ SSH连接成功，可显示服务器欢迎信息和提示符
- ✅ 实现ANSI颜色支持
- ✅ 完成所有键盘按键绑定（字母、数字、符号、方向键、Ctrl组合键等）
- ✅ 实现焦点切换机制（Ctrl+T）
- ✅ 条件显示聊天输入框
- ❌ **焦点管理失败** - prompt_toolkit不支持`focus(None)`
- 🔴 **终端无法接收输入** - TextArea组件与键绑定冲突

**问题总结**:
prompt_toolkit的Widget体系与我们的"虚拟终端"设计理念不匹配。需要找到合适的方法让键盘事件直接到达我们的键绑定处理器，而不被TextArea拦截。

**下一步方向：**
1. 研究创建自定义的focusable容器
2. 或考虑使用单一的隐藏TextArea作为输入源
3. 或完全重构为模态UI（终端/聊天二选一）

---

更新时间：2025-10-21 晚
