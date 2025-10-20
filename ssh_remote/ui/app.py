"""Main Textual application for SSH Remote Assistant."""

import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding
from ssh_remote.models import Server, AuthMethod
from ssh_remote.core.ssh_manager import SSHConnection


class SSHTerminalPanel(Static):
    """Left panel showing SSH terminal output."""
    
    def __init__(self):
        super().__init__()
        self.output_lines: list[str] = []
    
    def compose(self) -> ComposeResult:
        yield Static("SSH Terminal Output", classes="panel-title")
        yield Static("", id="terminal-content", classes="terminal-output")
        yield Input(placeholder="输入SSH命令 (例如: ls -la)...", id="terminal-input")
    
    def add_output(self, text: str):
        """Add text to terminal output."""
        self.output_lines.append(text)
        # Keep last 100 lines
        if len(self.output_lines) > 100:
            self.output_lines = self.output_lines[-100:]
        
        terminal = self.query_one("#terminal-content", Static)
        terminal.update("\n".join(self.output_lines))


class ChatPanel(Static):
    """Right panel for AI chat interface."""
    
    def __init__(self):
        super().__init__()
        self.messages: list[tuple[str, str]] = []  # (role, content)
    
    def compose(self) -> ComposeResult:
        yield Static("AI Chat Assistant", classes="panel-title")
        yield Static("", id="chat-content", classes="chat-output")
        yield Input(placeholder="输入你的需求...", id="chat-input")
    
    def add_message(self, role: str, content: str):
        """Add a message to chat history."""
        self.messages.append((role, content))
        self._update_display()
    
    def _update_display(self):
        """Update the chat display."""
        chat_content = self.query_one("#chat-content", Static)
        
        formatted_messages = []
        for role, content in self.messages:
            prefix = "You: " if role == "user" else "AI: "
            formatted_messages.append(f"{prefix}{content}")
        
        chat_content.update("\n\n".join(formatted_messages))


class SSHRemoteApp(App):
    """Main SSH Remote Assistant application."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    SSHTerminalPanel {
        width: 50%;
        border: solid green;
        padding: 1;
    }
    
    ChatPanel {
        width: 50%;
        border: solid blue;
        padding: 1;
    }
    
    .panel-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .terminal-output {
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
    }
    
    .chat-output {
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
    }
    
    #chat-input {
        dock: bottom;
    }
    
    #terminal-input {
        dock: bottom;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "SSH Remote Assistant"
        self.sub_title = "AI-powered command execution"
        self.ssh_connection = None
        self.server = None
        self.server_password = None
    
    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        
        with Container(id="main-container"):
            yield SSHTerminalPanel()
            yield ChatPanel()
        
        yield Footer()
    
    def on_mount(self):
        """Called when app is mounted."""
        # Add welcome messages
        terminal = self.query_one(SSHTerminalPanel)
        terminal.add_output("欢迎使用 SSH Remote Assistant!")
        terminal.add_output("正在加载服务器配置...")
        
        chat = self.query_one(ChatPanel)
        chat.add_message("assistant", "你好！我是你的AI助手。告诉我你想在服务器上做什么，我会帮你生成命令。")
        
        # Load server config and connect
        self.load_and_connect()
    
    def load_and_connect(self):
        """Load server config and establish connection."""
        terminal = self.query_one(SSHTerminalPanel)
        
        try:
            # Load config file
            config_path = Path("server_config.json")
            if not config_path.exists():
                terminal.add_output("❌ 错误: 找不到 server_config.json 配置文件")
                terminal.add_output("请在项目根目录创建配置文件")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            server_config = config['server']
            
            # Create server model
            self.server = Server(
                name=server_config['name'],
                host=server_config['host'],
                port=server_config.get('port', 22),
                username=server_config['username'],
                auth_method=AuthMethod(server_config.get('auth_method', 'password')),
                key_path=server_config.get('key_path')
            )
            
            self.server_password = server_config.get('password')
            
            terminal.add_output(f"📡 正在连接到 {self.server.name} ({self.server.host})...")
            
            # Establish SSH connection
            self.ssh_connection = SSHConnection(self.server)
            self.ssh_connection.connect(password=self.server_password)
            
            terminal.add_output(f"✅ 成功连接到 {self.server.host}")
            terminal.add_output(f"👤 用户: {self.server.username}")
            terminal.add_output("")
            terminal.add_output("💡 在左侧输入框输入命令 (例如: ls -la)")
            
            self.sub_title = f"Connected to {self.server.name}"
            
        except FileNotFoundError:
            terminal.add_output("❌ 错误: server_config.json 文件不存在")
        except KeyError as e:
            terminal.add_output(f"❌ 配置文件格式错误: 缺少 {e}")
        except Exception as e:
            terminal.add_output(f"❌ 连接失败: {str(e)}")
    
    def execute_ssh_command(self, command: str):
        """Execute a command via SSH."""
        terminal = self.query_one(SSHTerminalPanel)
        
        if not self.ssh_connection or not self.ssh_connection.is_connected:
            terminal.add_output("❌ 未连接到服务器")
            return
        
        try:
            terminal.add_output(f"\n$ {command}")
            stdout, stderr, exit_code = self.ssh_connection.execute_command(command)
            
            if stdout:
                terminal.add_output(stdout.rstrip())
            if stderr:
                terminal.add_output(f"[stderr] {stderr.rstrip()}")
            if exit_code != 0:
                terminal.add_output(f"[exit code: {exit_code}]")
                
        except Exception as e:
            terminal.add_output(f"❌ 命令执行失败: {str(e)}")
    
    def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission."""
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Handle terminal input (SSH commands)
        if event.input.id == "terminal-input":
            self.execute_ssh_command(user_input)
            event.input.value = ""
            return
        
        # Handle chat input (AI chat)
        if event.input.id == "chat-input":
            chat = self.query_one(ChatPanel)
            chat.add_message("user", user_input)
            event.input.value = ""
            
            # TODO: Process with AI and execute commands
            # For now, just echo back
            chat.add_message("assistant", f"收到你的需求：{user_input}\n（AI集成开发中...）")
            return
    
    def on_unmount(self):
        """Called when app is unmounted."""
        if self.ssh_connection:
            self.ssh_connection.disconnect()


if __name__ == "__main__":
    app = SSHRemoteApp()
    app.run()
