"""Terminal application using prompt_toolkit and pyte."""

import asyncio
import json
from pathlib import Path
from typing import Optional, Callable

import pyte
import paramiko
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    HSplit,
    VSplit,
    Window,
    Layout,
    FormattedTextControl,
    UIControl,
    UIContent,
    ConditionalContainer,
    FloatContainer,
    Float,
)
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.formatted_text import ANSI, HTML
from prompt_toolkit.filters import Condition

from ssh_remote.models import Server, AuthMethod
from ssh_remote.services.ai_service import AIAssistant


class TerminalInputControl(UIControl):
    """
    自定义的终端控件：显示SSH终端输出
    
    注意：键盘输入由全局键绑定处理（带条件过滤器）
    这个控件只负责显示内容
    """
    
    def __init__(self, terminal_text_getter: Callable[[], str]):
        """
        Args:
            terminal_text_getter: 获取终端显示文本的函数
        """
        self.terminal_text_getter = terminal_text_getter
    
    def create_content(self, width: int, height: int) -> UIContent:
        """
        创建显示内容：显示SSH终端输出（带ANSI颜色）
        """
        terminal_text = self.terminal_text_getter()
        
        # 将文本分割成行
        lines = terminal_text.split('\n')
        
        # 确保至少有 height 行
        while len(lines) < height:
            lines.append('')
        
        # 只取需要的行数
        lines = lines[:height]
        
        def get_line(i):
            if i < len(lines):
                # ANSI 对象需要转换为 formatted text 列表
                # ANSI 对象本身就是一个可迭代的 formatted text
                # 但我们需要调用它来获取片段列表
                ansi_text = ANSI(lines[i])
                # ANSI 类实现了 __pt_formatted_text__() 方法
                # 直接返回它即可，prompt_toolkit 会自动处理
                return ansi_text.__pt_formatted_text__()
            return []
        
        return UIContent(
            get_line=get_line,
            line_count=len(lines),
            cursor_position=None,  # 光标由SSH服务器控制
        )
    
    def is_focusable(self) -> bool:
        """允许获得焦点"""
        return True
    
    def mouse_handler(self, mouse_event):
        """鼠标事件处理（可选）"""
        return NotImplemented


class SSHTerminalSession:
    """SSH终端会话管理器（支持完整终端仿真）"""
    
    def __init__(self, server: Server, password: Optional[str] = None):
        self.server = server
        self.password = password
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None
        self.connected = False
        
        # pyte 终端模拟器
        self.cols = 120
        self.rows = 40
        self.screen = pyte.Screen(self.cols, self.rows)
        self.stream = pyte.Stream(self.screen)
        
        # 输出缓冲区（用于保存原始ANSI输出）
        self.output_buffer = ""
        
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
                width=self.cols,
                height=self.rows
            )
            
            # 设置为非阻塞模式
            self.channel.setblocking(0)
            
            self.connected = True
            
            # 等待初始提示符（重要！）
            import time
            time.sleep(0.3)  # 给服务器时间发送初始输出
            
            # 立即读取一次初始输出
            if self.channel.recv_ready():
                data = self.channel.recv(4096).decode('utf-8', errors='replace')
                self.output_buffer = data
                self.stream.feed(data)
            
            return True
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def resize(self, cols: int, rows: int):
        """调整终端大小"""
        self.cols = cols
        self.rows = rows
        self.screen.resize(rows, cols)
        if self.channel:
            self.channel.resize_pty(width=cols, height=rows)
    
    def send_input(self, data: str):
        """发送输入到SSH通道"""
        if self.channel and self.connected:
            self.channel.send(data)
    
    def send_key(self, key: str):
        """发送特殊按键"""
        key_map = {
            'enter': '\r',
            'backspace': '\x7f',
            'tab': '\t',
            'escape': '\x1b',
            'up': '\x1b[A',
            'down': '\x1b[B',
            'right': '\x1b[C',
            'left': '\x1b[D',
            'home': '\x1b[H',
            'end': '\x1b[F',
            'pageup': '\x1b[5~',
            'pagedown': '\x1b[6~',
            'delete': '\x1b[3~',
        }
        
        if key in key_map:
            self.send_input(key_map[key])
        else:
            self.send_input(key)
    
    def send_ctrl_key(self, char: str):
        """发送Ctrl组合键"""
        # Ctrl+字母对应的ASCII控制字符
        if len(char) == 1:
            code = ord(char.upper()) - ord('A') + 1
            if 1 <= code <= 26:
                self.send_input(chr(code))
    
    def read_output(self) -> str:
        """读取输出并更新终端屏幕"""
        if not self.channel or not self.connected:
            return ""
        
        try:
            if self.channel.recv_ready():
                data = self.channel.recv(4096).decode('utf-8', errors='replace')
                # 保存原始输出（包含ANSI颜色）
                self.output_buffer += data
                # 限制缓冲区大小
                if len(self.output_buffer) > 50000:
                    self.output_buffer = self.output_buffer[-40000:]
                # 更新终端屏幕
                self.stream.feed(data)
                return data
        except Exception as e:
            pass
        
        return ""
    
    def get_display(self) -> str:
        """获取当前屏幕显示内容（纯文本）"""
        lines = []
        for line_idx in range(self.screen.lines):
            line_text = ""
            for col_idx in range(self.screen.columns):
                if col_idx in self.screen.buffer[line_idx]:
                    line_text += self.screen.buffer[line_idx][col_idx].data
                else:
                    line_text += " "
            lines.append(line_text.rstrip())
        return "\n".join(lines)
    
    def get_colored_display(self) -> str:
        """获取带颜色的显示内容（ANSI转义序列）"""
        # 使用pyte屏幕缓冲区重建带颜色的输出
        lines = []
        for y in range(self.screen.lines):
            line_chars = []
            current_style = None
            
            for x in range(self.screen.columns):
                if x in self.screen.buffer[y]:
                    char = self.screen.buffer[y][x]
                    # 获取字符的样式（前景色、背景色、粗体等）
                    fg = char.fg if char.fg != 'default' else None
                    bg = char.bg if char.bg != 'default' else None
                    bold = char.bold
                    
                    # 构建新样式
                    new_style = (fg, bg, bold)
                    
                    # 如果样式改变，添加ANSI转义序列
                    if new_style != current_style:
                        # 重置之前的样式
                        if current_style is not None:
                            line_chars.append('\x1b[0m')
                        
                        # 应用新样式
                        if bold:
                            line_chars.append('\x1b[1m')
                        if fg:
                            # 简单的颜色映射（pyte使用颜色名称）
                            color_map = {
                                'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
                                'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,
                            }
                            if fg in color_map:
                                line_chars.append(f'\x1b[{color_map[fg]}m')
                        if bg:
                            color_map = {
                                'black': 40, 'red': 41, 'green': 42, 'yellow': 43,
                                'blue': 44, 'magenta': 45, 'cyan': 46, 'white': 47,
                            }
                            if bg in color_map:
                                line_chars.append(f'\x1b[{color_map[bg]}m')
                        
                        current_style = new_style
                    
                    line_chars.append(char.data)
                else:
                    line_chars.append(' ')
            
            # 重置行末样式
            if current_style is not None:
                line_chars.append('\x1b[0m')
            
            lines.append(''.join(line_chars).rstrip())
        
        return '\n'.join(lines)
    
    def get_cursor_position(self) -> tuple:
        """获取光标位置"""
        return (self.screen.cursor.y, self.screen.cursor.x)
    
    def disconnect(self):
        """断开连接"""
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()
        self.connected = False


class TerminalApp:
    """主应用程序（双面板：SSH终端 + AI聊天）"""
    
    def __init__(self):
        self.ssh_session: Optional[SSHTerminalSession] = None
        self.ai_assistant: Optional[AIAssistant] = None
        self.running = False
        self.terminal_focused = True  # 焦点状态：True=终端，False=聊天
        
        # 终端显示文本
        self.terminal_text = ""
        
        # ⭐ 创建自定义的终端控件（只负责显示）
        # 输入由全局键绑定处理
        self.terminal_input_control = TerminalInputControl(
            terminal_text_getter=lambda: self.terminal_text,
        )
        
        # AI聊天区域（只读）
        self.chat_area = TextArea(
            text="",
            multiline=True,
            read_only=True,
            scrollbar=True,
            focusable=False,  # 禁止聊天历史获得焦点
        )
        
        # AI输入框（仅在聊天模式可用）
        self.input_field = TextArea(
            height=3,
            prompt="AI>>> ",
            multiline=False,
            wrap_lines=False,
            focusable=True,
        )
        
        # 状态栏文本
        self.status_text = "正在加载..."
        
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
            enable_page_navigation_bindings=False,
        )
    
    def _create_layout(self) -> Layout:
        """创建应用布局（双面板+状态栏）"""
        
        # ⭐ 左侧：SSH终端窗口
        # 显示由自定义控件处理，输入由全局键绑定+条件过滤器处理
        self.terminal_input_window = Window(
            content=self.terminal_input_control,
            wrap_lines=False,
            always_hide_cursor=False,
        )
        
        terminal_window = Frame(
            self.terminal_input_window,
            title=lambda: "🖥️  SSH Terminal" + (" [FOCUS]" if self.terminal_focused else ""),
        )
        
        # 右侧：AI聊天
        chat_container = HSplit([
            Frame(self.chat_area, title="💬 Chat History"),
            # 输入框只在聊天模式下可见并可用
            ConditionalContainer(
                Frame(self.input_field, title="✏️  Your Message"),
                filter=Condition(lambda: not self.terminal_focused)
            ),
            # 终端模式下显示提示信息
            ConditionalContainer(
                Window(
                    content=FormattedTextControl(
                        text="🖥️  Terminal Mode - Press Ctrl+T to switch to Chat"
                    ),
                    height=3,
                    style="bg:#333333 #888888",
                ),
                filter=Condition(lambda: self.terminal_focused)
            ),
        ])
        
        # 状态栏
        status_bar = Window(
            content=FormattedTextControl(
                text=lambda: HTML(self.status_text)
            ),
            height=1,
            style="bg:#444444 #ffffff",
        )
        
        # 主布局：左右分栏 + 底部状态栏
        root = HSplit([
            VSplit([
                terminal_window,  # 左侧终端（60%宽度）
                chat_container,   # 右侧聊天（40%宽度）
            ]),
            status_bar,
        ])
        
        return Layout(root)
    
    def _switch_to_chat(self):
        """切换到聊天模式"""
        self.terminal_focused = False
        self._update_status()
        self.app.layout.focus(self.input_field)
    
    def _switch_to_terminal(self):
        """切换到终端模式"""
        self.terminal_focused = True
        self._update_status()
        # 直接聚焦到我们保存的输入窗口
        self.app.layout.focus(self.terminal_input_window)
    
    def _create_key_bindings(self) -> KeyBindings:
        """创建全局按键绑定"""
        kb = KeyBindings()
        
        # ========== 条件过滤器 ==========
        is_terminal_focused = Condition(lambda: self.terminal_focused)
        is_chat_focused = Condition(lambda: not self.terminal_focused)
        
        # ========== 终端模式的所有按键（从 TerminalInputControl 复制过来）==========
        # ⭐ 关键改变：将控件的键绑定移到全局，并添加 filter 条件
        
        @kb.add('c-q', filter=is_terminal_focused)
        def _(event):
            """Ctrl+Q: 退出应用（终端模式）"""
            event.app.exit()
        
        @kb.add('c-t', filter=is_terminal_focused)
        def _(event):
            """Ctrl+T: 切换到聊天模式"""
            self._switch_to_chat()
        
        # 功能键
        @kb.add('enter', filter=is_terminal_focused)
        def _(event):
            if self.ssh_session and self.ssh_session.connected:
                self.ssh_session.send_key('enter')
        
        @kb.add('backspace', filter=is_terminal_focused)
        def _(event):
            if self.ssh_session and self.ssh_session.connected:
                self.ssh_session.send_key('backspace')
        
        @kb.add('tab', filter=is_terminal_focused)
        def _(event):
            if self.ssh_session and self.ssh_session.connected:
                self.ssh_session.send_key('tab')
        
        @kb.add('escape', filter=is_terminal_focused)
        def _(event):
            if self.ssh_session and self.ssh_session.connected:
                self.ssh_session.send_key('escape')
        
        # 方向键
        for key in ['up', 'down', 'left', 'right', 'home', 'end', 'pageup', 'pagedown', 'delete']:
            @kb.add(key, filter=is_terminal_focused)
            def _(event, k=key):
                if self.ssh_session and self.ssh_session.connected:
                    self.ssh_session.send_key(k)
        
        # Ctrl 组合键（除了 Q 和 T）
        for char in 'abcdefghijklmnoprsuvwxyz':  # 排除 q, t
            @kb.add(f'c-{char}', filter=is_terminal_focused)
            def _(event, c=char):
                if self.ssh_session and self.ssh_session.connected:
                    self.ssh_session.send_ctrl_key(c)
        
        # 普通字符（使用 <any> 通配符）
        @kb.add('<any>', filter=is_terminal_focused)
        def _(event):
            if self.ssh_session and self.ssh_session.connected:
                key = event.key_sequence[0].key
                # 确保是单个字符
                if len(key) == 1:
                    self.ssh_session.send_input(key)
        
        # ========== 聊天模式的快捷键 ==========
        
        @kb.add('c-q', filter=is_chat_focused)
        def _(event):
            """Ctrl+Q: 退出应用（聊天模式）"""
            event.app.exit()
        
        @kb.add('c-t', filter=is_chat_focused)
        def _(event):
            """Ctrl+T: 切换到终端模式"""
            self._switch_to_terminal()
        
        @kb.add('enter', filter=is_chat_focused)
        async def _(event):
            """Enter: 发送AI消息"""
            await self._handle_ai_input()
        
        return kb
    
    def _update_status(self):
        """更新状态栏"""
        if self.ssh_session and self.ssh_session.connected:
            server_info = f"{self.ssh_session.server.username}@{self.ssh_session.server.host}"
            focus_mode = "🖥️ Terminal" if self.terminal_focused else "💬 Chat"
            self.status_text = f"<b>{server_info}</b> | Mode: <b>{focus_mode}</b> | Ctrl+T: Switch | Ctrl+Q: Quit"
        else:
            self.status_text = "未连接 | Ctrl+Q: Quit"
    
    async def _handle_ai_input(self):
        """处理AI输入"""
        user_input = self.input_field.text.strip()
        if not user_input:
            return
        
        # 清空输入框
        self.input_field.text = ""
        
        # 添加用户消息到聊天区
        current_chat = self.chat_area.text
        self.chat_area.text = current_chat + f"\n\n🧑 You: {user_input}"
        
        try:
            if self.ai_assistant:
                # TODO: 调用AI生成命令
                # 这里先显示一个占位消息
                self.chat_area.text += f"\n\n🤖 AI: 收到！正在分析您的需求...\n（AI功能开发中）"
            else:
                self.chat_area.text += f"\n\n⚠️ AI助手未初始化（请配置OPENAI_API_KEY）"
        except Exception as e:
            self.chat_area.text += f"\n\n❌ 错误: {str(e)}"
    
    async def load_config_and_connect(self):
        """加载配置并连接SSH"""
        try:
            config_path = Path("server_config.json")
            if not config_path.exists():
                self.terminal_text = "❌ 错误: 找不到 server_config.json"
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
            
            self.terminal_text = f"正在连接到 {server.host}..."
            
            # 连接
            if self.ssh_session.connect():
                # 等待并读取更多初始输出
                await asyncio.sleep(0.5)  # 给服务器更多时间
                self.ssh_session.read_output()  # 再次读取
                
                # 获取初始终端输出（包括提示符）
                self.terminal_text = self.ssh_session.get_colored_display()
                
                # 如果还是空的，显示一个提示
                if not self.terminal_text.strip():
                    self.terminal_text = "🖥️  已连接到服务器，等待输出...\n(尝试按 Enter 键显示提示符)"
                
                self.chat_area.text = "👋 你好！我是AI助手。\n\n📌 使用指南:\n• 左侧是SSH终端，可以直接输入命令\n• 右侧可以向我描述需求，我会帮你生成命令\n• 按 Ctrl+T 切换左右面板焦点\n• 按 Ctrl+Q 退出应用"
                
                # 初始化AI助手（如果配置了API Key）
                try:
                    from ssh_remote.config import settings
                    if settings.OPENAI_API_KEY:
                        self.ai_assistant = AIAssistant()
                        self.chat_area.text += "\n\n✅ AI助手已就绪"
                    else:
                        self.chat_area.text += "\n\n⚠️ 未配置OPENAI_API_KEY，AI功能将不可用"
                except Exception as e:
                    self.chat_area.text += f"\n\n⚠️ AI初始化失败: {str(e)}"
                
                self._update_status()
                return True
            else:
                self.terminal_text = "❌ 连接失败"
                return False
                
        except Exception as e:
            self.terminal_text = f"❌ 错误: {str(e)}"
            return False
    
    async def update_terminal_display(self):
        """更新终端显示（实时刷新）"""
        while self.running:
            if self.ssh_session and self.ssh_session.connected:
                # 读取SSH输出
                output = self.ssh_session.read_output()
                
                # 始终更新显示（即使没有新输出，也要反映当前屏幕状态）
                self.terminal_text = self.ssh_session.get_colored_display()
                
                # 始终刷新UI（确保用户输入能实时显示）
                self.app.invalidate()
            
            await asyncio.sleep(0.05)  # 20fps刷新率
    
    def run(self):
        """运行应用"""
        self.running = True
        
        # 先连接SSH
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.load_config_and_connect())
        
        # 启动显示更新任务
        asyncio.ensure_future(self.update_terminal_display())
        
        # 设置初始焦点到终端输入控件
        self._switch_to_terminal()
        
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
