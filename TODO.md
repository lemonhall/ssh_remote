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

#### 新UI架构 (`ui/terminal_app.py`) - ✅ 方案B实现完成
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

### 🔴 问题仍未解决 (2025-10-21 深夜 - 第三/四轮尝试)

#### 方案B的多次尝试 - 均失败 ❌

**尝试1：UIControl + get_key_bindings()**
- 创建 `TerminalInputControl` 继承 `UIControl`
- 在 `create_content()` 中渲染SSH终端输出
- 在 `get_key_bindings()` 中处理键盘输入
- **失败原因**：`UIControl.get_key_bindings()` 似乎不会被自动调用

**尝试2：UIControl + Window.key_bindings**
- 尝试将控件的键绑定附加到 Window 上
- **失败原因**：Window 构造函数不接受 key_bindings 参数

**尝试3：全局键绑定 + Condition 过滤器**
- 将所有终端输入移到全局键绑定
- 使用 `Condition(lambda: self.terminal_focused)` 过滤
- **失败原因**：仍然无法捕获输入（原因不明）

**技术困境**：
- ✅ 显示正常：SSH连接成功，终端内容显示正确
- ✅ 焦点管理正常：可以用 Ctrl+T 切换焦点
- ✅ 聊天输入正常：右侧 TextArea 可以输入
- ❌ **终端输入失败**：左侧终端窗口无法接收任何输入

**可能的根本原因**：
1. prompt_toolkit 的焦点机制可能需要 `BufferControl` 或 `TextArea`
2. 自定义 `UIControl` 可能默认不参与键盘输入处理
3. 全局键绑定的优先级可能低于某些内置处理器
4. 可能需要研究 prompt_toolkit 的 `KeyProcessor` 机制

#### 已尝试但失败的所有方案总结
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

**已尝试的所有方案**：

- ❌ **方案A（已废弃）**: TextArea + 虚拟控件转发
  - TextArea 的 BufferControl 优先级太高，无法拦截输入
  
- ❌ **方案B（多次尝试，均失败）**: 自定义 UIControl
  - 尝试1：控件级键绑定 - 不生效
  - 尝试2：Window级键绑定 - 不支持
  - 尝试3：全局键绑定+过滤器 - 仍无法捕获输入
  - **核心问题**：自定义UIControl似乎不参与键盘输入事件流

- ⏸️ **方案C（未尝试）**: input_processors 拦截
  - 理论可行性低，可能仍会被 Buffer 消费

- 🎯 **方案D（强烈推荐，下次尝试）**: 全屏模式切换
  - 放弃双面板同时交互
  - 终端模式：全屏SSH终端（使用原生TextArea或其他方案）
  - 聊天模式：全屏AI对话
  - Ctrl+T 切换布局
  - **优势**：简单可靠，避开复杂的焦点问题

- ⏸️ **方案E（备选）**: 使用 BufferControl + 自定义处理
  - 研究 prompt_toolkit 的 `BufferControl` 源码
  - 创建自定义 Buffer，拦截输入事件
  - 可能需要深入理解 KeyProcessor 机制

- ⏸️ **方案F（最后手段）**: 使用 curses 或其他底层库
  - 完全放弃 prompt_toolkit
  - 使用 `curses` 或 `blessed` 等更底层的TUI库
  - 完全掌控输入输出

## 📋 下一步计划（第四轮重新规划）

### 🎯 优先级1: 彻底解决终端输入问题

**下次必须采用方案D（全屏模式切换）🚀**

方案B已经尝试了多次，均失败。prompt_toolkit的键盘输入机制比想象中复杂：
- 自定义UIControl似乎不参与输入事件流
- 全局键绑定在某些情况下也无法捕获输入
- 可能需要深入研究KeyProcessor和Buffer机制

**方案D实施步骤**：
1. [ ] 创建两套完全独立的布局：
   - `terminal_layout`：全屏SSH终端
   - `chat_layout`：全屏AI聊天
   
2. [ ] 终端布局的实现方案（三选一）：
   - [ ] **方案D1**: 使用 TextArea（最简单）
     - 让TextArea只读，但用全局键绑定捕获输入
     - 或者让TextArea可写，然后拦截其Buffer变化
   - [ ] **方案D2**: 使用原生的命令行输入
     - 研究 `PromptSession` 的使用
   - [ ] **方案D3**: 研究其他SSH客户端的实现
     - 参考 `asyncssh` 或 `fabric` 的TUI实现
   
3. [ ] Ctrl+T 切换 `app.layout` 在两个布局之间
   
4. [ ] 如果方案D成功，再考虑是否优化回双面板

**为什么方案D一定能成功**：
- 全屏模式下，不需要复杂的焦点管理
- 可以使用TextArea的原生输入能力
- 如果TextArea还不行，至少可以用简单的输入提示符（类似传统SSH客户端）

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

**2025-10-21 深夜第三轮**:
- ✅ 创建自定义 `TerminalInputControl` 继承 `UIControl`
- ✅ 在控件中实现显示和键绑定
- ✅ 修复 ANSI 格式化问题（`__pt_formatted_text__()`）
- ✅ 程序可以启动，界面显示正常
- ❌ **输入仍然无效** - 控件的 `get_key_bindings()` 似乎不生效

**2025-10-21 深夜第四轮**:
- ✅ 将键绑定从控件移到全局
- ✅ 使用 `Condition(lambda: self.terminal_focused)` 过滤器
- ✅ 简化 `TerminalInputControl` 只负责显示
- ❌ **输入仍然无效** - 全局键绑定在终端窗口获得焦点时也不工作

**核心问题未解决**:
prompt_toolkit 的键盘输入处理机制比想象中复杂。自定义 UIControl 无法像 TextArea 那样自然地接收输入事件。可能的原因：
1. 需要特殊的 `BufferControl` 或类似机制
2. 键盘事件的处理链路中，自定义控件的优先级不够
3. 可能需要实现更底层的 `KeyProcessor` 或事件处理器

**结论**:
方案B（自定义UIControl）在当前知识水平下无法实现。必须转向方案D（全屏模式切换），或者深入研究 prompt_toolkit 源码找到正确的实现方式。

---

更新时间：2025-10-21 深夜（多轮调试后）
