"""Terminal application using prompt_toolkit and pyte."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import pyte
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    HSplit,
    VSplit,
    Window,
    Layout,
    FormattedTextControl,
)
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit import print_formatted_text
import paramiko

from ssh_remote.models import Server, AuthMethod


class SSHTerminalSession:
    """SSH终端会话管理器"""
    
    def __init__(self, server: Server, password: Optional[str] = None):
        self.server = server
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self.connected = False
        
        # pyte 终端模拟器
        self.screen = pyte.Screen(120, 40)  # 默认大小
        self.stream = pyte.Stream(self.screen)
        
    def connect(self) -> bool:
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.server.host,
                "port": self.server.port,
                "username": self.server.username,
                "timeout": 30,
            }
            
            if self.server.auth_method == AuthMethod.KEY and self.server.key_path:
                connect_kwargs["key_filename"] = self.server.key_path
            elif self.password:
                connect_kwargs["password"] = self.password
            
            self.client.connect(**connect_kwargs)
            
            # 创建交互式shell通道
            self.channel = self.client.invoke_shell(
                term='xterm-256color',
                width=120,
                height=40
            )
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def resize(self, cols: int, rows: int):
        """调整终端大小"""
        self.screen.resize(rows, cols)
        if self.channel:
            self.channel.resize_pty(width=cols, height=rows)
    
    def send_input(self, data: str):
        """发送输入到SSH通道"""
        if self.channel and self.connected:
            self.channel.send(data)
    
    def read_output(self) -> str:
        """读取输出并更新终端屏幕"""
        if not self.channel or not self.connected:
            return ""
        
        if self.channel.recv_ready():
            data = self.channel.recv(4096).decode('utf-8', errors='replace')
            self.stream.feed(data)
            return data
        return ""
    
    def get_display(self) -> list:
        """获取当前屏幕显示内容"""
        lines = []
        for line_idx in range(self.screen.lines):
            line_text = ""
            for char in self.screen.buffer[line_idx].values():
                line_text += char.data
            lines.append(line_text)
        return lines
    
    def disconnect(self):
        """断开连接"""
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()
        self.connected = False


class TerminalApp:
    """主应用程序"""
    
    def __init__(self):
        self.ssh_session: Optional[SSHTerminalSession] = None
        self.running = False
        
        # 创建UI组件
        self.terminal_display = FormattedTextControl(text="正在加载...")
        self.chat_area = TextArea(
            text="",
            multiline=True,
            read_only=True,
            scrollbar=True,
        )
        self.input_field = TextArea(
            height=3,
            prompt=">>> ",
            multiline=False,
        )
        
        # 创建布局
        self.layout = self._create_layout()
        
        # 创建按键绑定
        self.kb = self._create_key_bindings()
        
        # 创建应用
        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
        )
    
    def _create_layout(self) -> Layout:
        """创建应用布局"""
        
        # 左侧：SSH终端
        terminal_window = Frame(
            Window(content=self.terminal_display, wrap_lines=False),
            title="SSH Terminal",
        )
        
        # 右侧：AI聊天
        chat_window = Frame(
            VSplit([
                Window(content=self.chat_area.control, wrap_lines=True),
                self.input_field,
            ]),
            title="AI Assistant",
        )
        
        # 主布局：左右分栏
        root = HSplit([
            VSplit([
                terminal_window,  # 左侧终端
                chat_window,      # 右侧聊天
            ]),
        ])
        
        return Layout(root)
    
    def _create_key_bindings(self) -> KeyBindings:
        """创建按键绑定"""
        kb = KeyBindings()
        
        @kb.add('c-c')
        def _(event):
            """Ctrl-C 退出"""
            event.app.exit()
        
        @kb.add('c-q')
        def _(event):
            """Ctrl-Q 退出"""
            event.app.exit()
        
        return kb
    
    async def load_config_and_connect(self):
        """加载配置并连接SSH"""
        try:
            config_path = Path("server_config.json")
            if not config_path.exists():
                self.terminal_display.text = "❌ 错误: 找不到 server_config.json"
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            server_config = config['server']
            
            server = Server(
                name=server_config['name'],
                host=server_config['host'],
                port=server_config.get('port', 22),
                username=server_config['username'],
                auth_method=AuthMethod(server_config.get('auth_method', 'password')),
                key_path=server_config.get('key_path')
            )
            
            password = server_config.get('password')
            
            # 创建SSH会话
            self.ssh_session = SSHTerminalSession(server, password)
            
            self.terminal_display.text = f"正在连接到 {server.host}..."
            
            # 连接
            if self.ssh_session.connect():
                self.terminal_display.text = f"✅ 已连接到 {server.host}"
                self.chat_area.text = "你好！我是AI助手。\n\n左侧是SSH终端，你可以直接输入命令。\n右侧可以向我描述需求，我会帮你生成命令。"
                return True
            else:
                self.terminal_display.text = "❌ 连接失败"
                return False
                
        except Exception as e:
            self.terminal_display.text = f"❌ 错误: {str(e)}"
            return False
    
    async def update_terminal_display(self):
        """更新终端显示"""
        while self.running:
            if self.ssh_session and self.ssh_session.connected:
                # 读取SSH输出
                self.ssh_session.read_output()
                
                # 更新显示
                lines = self.ssh_session.get_display()
                self.terminal_display.text = "\n".join(lines)
                
                # 刷新UI
                self.app.invalidate()
            
            await asyncio.sleep(0.05)  # 20fps
    
    def run(self):
        """运行应用"""
        self.running = True
        
        # 先连接SSH
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.load_config_and_connect())
        
        # 启动显示更新任务
        asyncio.ensure_future(self.update_terminal_display())
        
        # 运行应用
        try:
            self.app.run()
        finally:
            self.running = False
            if self.ssh_session:
                self.ssh_session.disconnect()


def main():
    """主入口"""
    app = TerminalApp()
    app.run()


if __name__ == "__main__":
    main()
