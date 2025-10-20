"""Main entry point for SSH Remote Assistant."""

from ssh_remote.ui.app import SSHRemoteApp


def run():
    """Run the SSH Remote Assistant application."""
    app = SSHRemoteApp()
    app.run()


if __name__ == "__main__":
    run()
