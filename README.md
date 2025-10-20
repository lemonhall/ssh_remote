# SSH Remote Assistant

AI-powered SSH command execution assistant with intelligent command generation.

## 快速开始

```bash
# 安装依赖
uv sync

# 配置API密钥（创建.env文件）
echo "OPENAI_API_KEY=your-api-key-here" > .env

# 运行应用
uv run ssh-remote
```

## 功能特性

- 🖥️ 双面板UI - SSH终端输出 + AI聊天界面
- 🤖 AI智能命令生成 - 理解你的需求，自动生成Shell命令
- 🔒 安全第一 - 危险命令检测，所有操作需确认
- 📝 命令历史 - 学习你的命令习惯
- 📦 命令模板 - 保存常用操作，一键执行
- 🌐 跨平台 - Windows/Linux/macOS完美支持

## 项目结构

```
ssh_remote/
├── core/           # 核心功能（SSH连接等）
├── services/       # 业务服务（AI服务等）
├── models/         # 数据模型
├── ui/             # 用户界面
├── config.py       # 配置管理
└── main.py         # 程序入口
```

查看 [DESIGN.md](DESIGN.md) 了解详细设计。
