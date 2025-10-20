# SSH Remote Assistant - TODO

## ✅ 已完成

### 核心模块
- [x] 项目初始化 (uv + pyproject.toml)
- [x] 配置管理 (`config.py`)
- [x] 数据模型 (`models/`)
- [x] SSH管理 (`core/ssh_manager.py`) - 支持交互式Shell
- [x] AI服务 (`services/ai_service.py`) - OpenAI集成

### UI重构 (`ui/terminal_app.py`)
- [x] 迁移到 prompt_toolkit + pyte
- [x] SSH连接和终端显示
- [x] 焦点切换机制 (Ctrl+T)
- [x] 状态栏

## ✅ 最新进展 (2025-10-21 深夜)

### 方案F: FormattedTextControl + key_bindings ✅ 成功！
**突破**: 终端输入输出正常工作！

**关键发现**:
- ❌ BufferControl 会自动处理输入，即使设置了 key_bindings
- ✅ FormattedTextControl 完美支持 key_bindings
- ✅ 使用 lambda 动态获取内容，无需手动更新 Buffer
- ✅ 键绑定中立即读取+刷新，适应网络延迟

### 方案G: 异步刷新 + 光标显示 ✅ 体验大幅提升！
**核心改进**: 解决延迟问题，添加光标！

**关键优化**:
- ❌ 键绑定中同步等待 (time.sleep) 会阻塞UI线程
- ✅ 键绑定只发送，不等待 - 让后台循环处理
- ✅ 后台循环 100fps 超高频刷新 (10ms间隔)
- ✅ 添加闪烁光标显示 (500ms切换)
- ✅ 持续快速读取SSH输出，不依赖按键触发

**当前状态**:
- ✅ SSH 连接正常
- ✅ 键盘输入响应快速流畅
- ✅ 终端输出实时显示
- ✅ 光标闪烁，视觉反馈清晰
- ✅ 焦点切换 (Ctrl+T) 工作
- ✅ 网络延迟问题已解决

## 📋 下一步计划

### 优先级1: 清理和优化
- [ ] 移除所有调试代码
- [x] 优化网络延迟处理 ✅ 异步刷新解决
- [x] 添加光标显示 ✅ 闪烁光标实现
- [ ] 添加 ANSI 颜色支持（当前是纯文本）

### 优先级2: 终端功能完善
- [ ] ANSI 颜色显示（目前纯文本）
- [ ] 终端大小自适应
- [ ] 滚动缓冲区
- [ ] 光标显示

### 优先级3: AI聊天集成
- [ ] 右侧输入框功能
- [ ] AI命令生成
- [ ] 命令发送到终端执行

### 优先级4: 数据持久化
- [ ] 数据库模块 (SQLAlchemy)
- [ ] 服务器配置存储
- [ ] 命令历史记录

### 优先级5: 高级功能
- [ ] 命令模板系统
- [ ] 多服务器管理
- [ ] 安全增强 (密码加密、命令白名单)
- [ ] 命令确认机制

## � 快速开始

```powershell
uv sync                              # 安装依赖
# 编辑 server_config.json           # 配置服务器
# 编辑 .env                          # (可选) 配置 OpenAI API
uv run python -m ssh_remote.main     # 运行
```

## 🎯 技术栈

- **prompt_toolkit** - TUI框架
- **pyte** - VT100终端模拟器
- **paramiko** - SSH连接
- **OpenAI API** - AI命令生成

---

*更新时间: 2025-10-21*
