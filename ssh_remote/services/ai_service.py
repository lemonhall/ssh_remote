"""AI service for command generation and assistance."""

from typing import Optional
from openai import OpenAI
from ssh_remote.config import settings
from ssh_remote.models import ChatMessage


class AIAssistant:
    """AI assistant for command generation."""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        # 初始化 OpenAI 客户端，支持自定义 base_url
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        
        self.client = OpenAI(**client_kwargs)
        self.conversation_history: list[ChatMessage] = []
        self.command_history: list[str] = []
    
    def set_command_history(self, commands: list[str]):
        """Set the command history context."""
        self.command_history = commands
    
    def generate_command(
        self,
        user_input: str,
        context: Optional[str] = None
    ) -> tuple[str, list[str]]:
        """
        Generate command based on user input.
        
        Args:
            user_input: User's request
            context: Additional context (e.g., current directory)
            
        Returns:
            Tuple of (explanation, list of commands)
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Add user message to history
        user_msg = ChatMessage(role="user", content=user_input)
        self.conversation_history.append(user_msg)
        
        # Prepare messages for API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation_history
        ])
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )
        
        assistant_content = response.choices[0].message.content or ""
        
        # Add assistant response to history
        assistant_msg = ChatMessage(role="assistant", content=assistant_content)
        self.conversation_history.append(assistant_msg)
        
        # Parse response to extract commands
        explanation, commands = self._parse_response(assistant_content)
        
        return explanation, commands
    
    def _build_system_prompt(self, context: Optional[str] = None) -> str:
        """Build the system prompt with context."""
        prompt = """你是一个专业的Linux系统管理员助手。
你的任务是理解用户的运维需求，生成准确的Shell命令。

重要规则：
1. 生成的命令必须安全可靠
2. 对于危险操作，明确警告用户
3. 提供清晰的命令解释
4. 如果需要多步操作，按顺序列出
5. 命令格式：在代码块中列出，每行一个命令

用户的历史命令（供参考）：
"""
        
        if self.command_history:
            prompt += "\n".join(f"- {cmd}" for cmd in self.command_history[-20:])
        else:
            prompt += "（暂无历史命令）"
        
        if context:
            prompt += f"\n\n当前上下文：\n{context}"
        
        return prompt
    
    def _parse_response(self, response: str) -> tuple[str, list[str]]:
        """
        Parse AI response to extract explanation and commands.
        
        Returns:
            Tuple of (explanation, commands)
        """
        lines = response.strip().split("\n")
        commands = []
        explanation_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    commands.append(stripped)
            else:
                explanation_lines.append(line)
        
        explanation = "\n".join(explanation_lines).strip()
        
        return explanation, commands
    
    def check_dangerous_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Check if a command is potentially dangerous.
        
        Returns:
            Tuple of (is_dangerous, warning_message)
        """
        for dangerous_pattern in settings.dangerous_commands:
            if dangerous_pattern in command:
                return True, f"⚠️ 警告：此命令包含危险操作 '{dangerous_pattern}'"
        
        return False, None
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
