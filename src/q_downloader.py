import qbittorrentapi
import logging

class QBittorrentDownloader:
    def __init__(self, host="http://localhost", port=8080, username="admin", password=""):
        self.qbt_client = qbittorrentapi.Client(
            host=host,
            port=port,
            username=username,
            password=password
        )

    def check_connection(self):
        try:
            self.qbt_client.auth_log_in()
            return True
        except Exception as e:
            logging.error(f"qBittorrent connection failed: {e}")
            return False

    def add_magnet(self, magnet_link, save_path=None, category="AV-Downloader"):
        try:
            self.qbt_client.auth_log_in()
            self.qbt_client.torrents_add(
                urls=magnet_link,
                save_path=save_path,
                category=category
            )
            return True
        except Exception as e:
            logging.error(f"Error adding magnet to qBittorrent: {e}")
            return False

if __name__ == "__main__":
    # Test (requires qBittorrent running with Web UI enabled)
    downloader = QBittorrentDownloader()
    if downloader.check_connection():
        print("qBittorrent connected successfully.")
    else:
        print("Failed to connect to qBittorrent.")
