"""Main Textual application for SSH Remote Assistant."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, Button
from textual.binding import Binding


class SSHTerminalPanel(Static):
    """Left panel showing SSH terminal output."""
    
    def __init__(self):
        super().__init__()
        self.output_lines: list[str] = []
    
    def compose(self) -> ComposeResult:
        yield Static("SSH Terminal Output", classes="panel-title")
        yield Static("", id="terminal-content", classes="terminal-output")
    
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
        height: 100%;
        overflow-y: auto;
    }
    
    .chat-output {
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
    }
    
    #chat-input {
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
        terminal.add_output("等待连接服务器...")
        
        chat = self.query_one(ChatPanel)
        chat.add_message("assistant", "你好！我是你的AI助手。告诉我你想在服务器上做什么，我会帮你生成命令。")
    
    def on_input_submitted(self, event: Input.Submitted):
        """Handle chat input submission."""
        if event.input.id != "chat-input":
            return
        
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Add user message to chat
        chat = self.query_one(ChatPanel)
        chat.add_message("user", user_input)
        
        # Clear input
        event.input.value = ""
        
        # TODO: Process with AI and execute commands
        # For now, just echo back
        chat.add_message("assistant", f"收到你的需求：{user_input}\n（AI集成开发中...）")


if __name__ == "__main__":
    app = SSHRemoteApp()
    app.run()
