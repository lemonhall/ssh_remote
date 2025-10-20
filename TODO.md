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

**当前状态**:
- ✅ SSH 连接正常
- ✅ 键盘输入工作（所有字符、方向键、Ctrl组合键）
- ✅ 终端输出显示正常
- ✅ 焦点切换 (Ctrl+T) 工作
- ⚠️ 远程服务器（日本）有网络延迟，已优化重试机制

## 📋 下一步计划

### 优先级1: 清理和优化
- [ ] 移除所有调试代码
- [ ] 优化网络延迟处理
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
