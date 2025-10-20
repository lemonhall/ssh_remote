"""SSH connection management."""

from typing import Optional, Callable
import paramiko
import threading
import time
from ssh_remote.config import settings
from ssh_remote.models import Server


class SSHConnection:
    """Manages a single SSH connection."""
    
    def __init__(self, server: Server):
        self.server = server
        self.client: Optional[paramiko.SSHClient] = None
        self._connected = False
        self.shell_channel: Optional[paramiko.Channel] = None
        self._output_callback: Optional[Callable[[str], None]] = None
        self._output_thread: Optional[threading.Thread] = None
    
    def connect(self, password: Optional[str] = None) -> bool:
        """
        Establish SSH connection.
        
        Args:
            password: Password for authentication (if using password auth)
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": self.server.host,
                "port": self.server.port,
                "username": self.server.username,
                "timeout": settings.ssh_connection_timeout,
            }
            
            if self.server.auth_method == "key" and self.server.key_path:
                connect_kwargs["key_filename"] = self.server.key_path
            elif password:
                connect_kwargs["password"] = password
            
            self.client.connect(**connect_kwargs)
            self._connected = True
            return True
            
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect: {str(e)}")
    
    def execute_command(self, command: str) -> tuple[str, str, int]:
        """
        Execute a command on the remote server.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if not self._connected or not self.client:
            raise RuntimeError("Not connected to server")
        
        stdin, stdout, stderr = self.client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        
        return (
            stdout.read().decode("utf-8"),
            stderr.read().decode("utf-8"),
            exit_code
        )
    
    def start_shell(self, output_callback: Callable[[str], None]):
        """
        Start an interactive shell session.
        
        Args:
            output_callback: Function to call with shell output
        """
        if not self._connected or not self.client:
            raise RuntimeError("Not connected to server")
        
        self._output_callback = output_callback
        self.shell_channel = self.client.invoke_shell(term='xterm', width=120, height=40)
        
        # Start output reading thread
        self._output_thread = threading.Thread(target=self._read_shell_output, daemon=True)
        self._output_thread.start()
    
    def _read_shell_output(self):
        """Read output from shell in background thread."""
        try:
            while self.shell_channel and not self.shell_channel.closed:
                if self.shell_channel.recv_ready():
                    output = self.shell_channel.recv(4096).decode('utf-8', errors='replace')
                    if output and self._output_callback:
                        self._output_callback(output)
                else:
                    time.sleep(0.01)
        except Exception as e:
            if self._output_callback:
                self._output_callback(f"\n[Error reading output: {e}]\n")
    
    def send_to_shell(self, command: str):
        """
        Send a command to the interactive shell.
        
        Args:
            command: Command to send (will append newline)
        """
        if not self.shell_channel or self.shell_channel.closed:
            raise RuntimeError("Shell not started")
        
        # Send command with newline
        self.shell_channel.send(command + '\n')
    
    def disconnect(self):
        """Close the SSH connection."""
        if self.shell_channel:
            self.shell_channel.close()
        if self.client:
            self.client.close()
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
