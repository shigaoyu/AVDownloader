import aria2p
import logging

class Aria2Downloader:
    def __init__(self, host="http://127.0.0.1", port=6800, secret=""):
        self.client = aria2p.Client(
            host=host,
            port=port,
            secret=secret
        )
        self.aria2 = aria2p.API(self.client)

    def check_connection(self):
        try:
            self.aria2.get_version()
            return True
        except Exception as e:
            logging.error(f"Aria2 connection failed: {e}")
            return False

    def add_magnet(self, magnet_link, save_path=None):
        try:
            options = {}
            if save_path:
                options["dir"] = save_path
            
            download = self.aria2.add_magnet(magnet_link, options=options)
            return download.gid
        except Exception as e:
            logging.error(f"Error adding magnet: {e}")
            return None

    def get_download_status(self, gid):
        try:
            download = self.aria2.get_download(gid)
            return download.status
        except Exception:
            return "unknown"

if __name__ == "__main__":
    # Test (requires aria2c running)
    downloader = Aria2Downloader()
    if downloader.check_connection():
        print("Aria2 connected successfully.")
    else:
        print("Failed to connect to Aria2.")
