"""SSH connection management."""

from typing import Optional
import paramiko
from ssh_remote.config import settings
from ssh_remote.models import Server


class SSHConnection:
    """Manages a single SSH connection."""
    
    def __init__(self, server: Server):
        self.server = server
        self.client: Optional[paramiko.SSHClient] = None
        self._connected = False
    
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
    
    def disconnect(self):
        """Close the SSH connection."""
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
