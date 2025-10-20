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

### 🔴 当前问题 (2025-10-21 深夜 - 第二轮调试)

#### 阶段性进展
- ✅ 修复了 `focus(None)` 报错 → 创建虚拟 `dummy_control` TextArea
- ✅ SSH终端可以正常显示内容（欢迎信息、提示符、ANSI颜色）
- ✅ 状态栏正常，Ctrl+T 焦点切换不报错
- ✅ 右侧聊天面板可以正常输入（当焦点切换到聊天模式时）
- ❌ **左侧终端仍然无法接收键盘输入**

#### 核心问题：TextArea 的输入拦截机制
**已尝试的方案**：

**方案A（已测试 ❌ 失败）**: 隐藏 TextArea + 自定义键绑定
- 创建了高度为0的虚拟TextArea (`dummy_control`) 作为焦点目标
- 为其绑定了专用的 `_create_dummy_key_bindings()` 方法
- 使用 `<any>` 通配符捕获所有按键并转发到SSH
- **问题**：TextArea 的 `BufferControl` 优先级更高，在键绑定之前就消费了输入事件

**根本原因分析**：
- TextArea 内部有 `BufferControl` 和 `Buffer`，会优先处理所有输入
- 键绑定（KeyBindings）在处理链中优先级低于 Widget 内部处理器
- `control.key_bindings` 设置无效，因为 BufferControl 自己的处理器先执行
- prompt_toolkit 设计哲学：**拥有焦点的 Widget 控制输入，而非全局键绑定**

**教训**：
❌ TextArea 不适合作为"透明"的输入转发器
❌ 即使设置 `read_only=False` 也无法阻止其消费按键
❌ 使用 Filter 条件只能控制键绑定触发，但无法阻止 Widget 内部处理

**可行的解决方案**：

1. **方案B（推荐 ⭐）**: 自定义 UIControl 代替 TextArea
   - 创建一个继承 `UIControl` 的 `TerminalInputControl`
   - 重写 `create_content()` 返回空内容（不可见）
   - 在 `key_handler()` 中处理所有输入并转发到SSH
   - 完全掌控输入处理流程

2. **方案C**: 使用 input_processors 拦截
   - 为 dummy_control 添加自定义 `Processor`
   - 在 `apply_transformation()` 中拦截输入
   - 可能仍然会被 Buffer 消费

3. **方案D**: 全屏模式切换（最简单 🎯）
   - 放弃双面板同时交互
   - 终端模式：全屏SSH终端
   - 聊天模式：全屏AI对话
   - Ctrl+T 切换布局

4. **方案E**: 研究 `PromptSession` 集成
   - 使用 prompt_toolkit 的原生命令行输入
   - 输入直接管道到 SSH

## 📋 下一步计划（重新规划）

### 🎯 优先级1: 彻底解决终端输入问题
**必须二选一：**
- [ ] **方案B**: 实现自定义 UIControl（技术难度高，但最优雅）
- [ ] **方案D**: 改为全屏模式切换（最简单，立即可用）

**推荐先尝试方案D**：
1. 创建两套独立的布局（终端布局 + 聊天布局）
2. Ctrl+T 切换 `app.layout`
3. 终端布局使用真实的可输入 TextArea 或原生输入
4. 如果方案D可用，再考虑优化回双面板

### 优先级2: 基础功能完善
- [ ] 终端大小自适应
- [ ] 实时输出刷新优化
- [ ] 添加滚动缓冲区
  
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

**2025-10-21 晚上第一轮**:
- ✅ SSH连接成功，可显示服务器欢迎信息和提示符
- ✅ 实现ANSI颜色支持
- ✅ 完成所有键盘按键绑定（字母、数字、符号、方向键、Ctrl组合键等）
- ✅ 实现焦点切换机制（Ctrl+T）
- ✅ 条件显示聊天输入框
- ❌ **焦点管理失败** - prompt_toolkit不支持`focus(None)`
- 🔴 **终端无法接收输入** - TextArea组件与键绑定冲突

**2025-10-21 深夜第二轮**:
- ✅ 修复 `focus(None)` 错误 → 使用虚拟 dummy_control
- ✅ 终端显示完全正常（pyte渲染优化）
- ✅ 优化了 `get_colored_display()` 方法
- ✅ 为 dummy_control 添加专用键绑定
- ❌ **输入仍然无效** - TextArea的BufferControl优先级问题

**问题根源**:
TextArea 不是"透明"的输入容器。它的内部 BufferControl 会在键绑定之前消费所有输入事件。这是 prompt_toolkit 的设计哲学：Widget 拥有输入控制权，而非全局键绑定。

**结论**:
必须放弃使用 TextArea 作为输入转发器。要么实现自定义 UIControl，要么改用全屏模式切换。

---

更新时间：2025-10-21 晚
