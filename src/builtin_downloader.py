import subprocess
import os
import sys

class BuiltinDownloader:
    """
    A lightweight CLI downloader using 'aria2c'.
    Works on Mac (via brew) and Windows (via exe in PATH).
    """
    def __init__(self, save_path="./downloads"):
        self.save_path = os.path.abspath(save_path)
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        
        # Check if aria2c is available
        self.has_aria2 = self._check_command("aria2c")

    def _check_command(self, cmd):
        try:
            # Check if command exists
            subprocess.run([cmd, "--version"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False

    def check_connection(self):
        return self.has_aria2

    def add_magnet(self, magnet_link, save_path=None):
        if not save_path:
            save_path = self.save_path
            
        if not self.has_aria2:
            return False

        # For the direct downloader, we don't just "add", we'll run it.
        # This method just confirms we are ready.
        return True

    def download_sync(self, magnet_link, title=""):
        """
        Executes aria2c synchronously to show progress in terminal.
        """
        if not self.has_aria2:
            print("\n[ERROR] aria2c not found! Please install it first:")
            print("  Mac: brew install aria2")
            print("  Win: Download aria2c.exe and add to PATH")
            return False

        print(f"\n[Aria2] Downloading: {title}")
        print(f"[Aria2] Saving to: {self.save_path}")
        print("-" * 50)
        
        # --seed-time=0: Stop seeding after download
        # --summary-interval=1: Update status every second
        cmd = [
            "aria2c", 
            magnet_link, 
            "--dir", self.save_path, 
            "--seed-time=0", 
            "--summary-interval=1",
            "--console-log-level=warn"
        ]
        
        try:
            # Run and pipe output directly to current terminal
            process = subprocess.Popen(cmd)
            process.wait()
            return process.returncode == 0
        except KeyboardInterrupt:
            print("\n[Aria2] Download paused by user. Run again to resume.")
            if 'process' in locals():
                process.terminate()
            return False
        except Exception as e:
            print(f"\n[Aria2] Critical Error: {e}")
            return False
