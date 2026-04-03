import subprocess
import os
import threading
import json
import time

class WebTorrentDownloader:
    """
    Downloader using webtorrent-cli (via npx).
    EXTREMELY good at magnets and peer discovery on Mac.
    """
    def __init__(self, save_path="./downloads"):
        self.save_path = os.path.abspath(save_path)
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        self.tasks = {} # gid -> process

    def add_magnet(self, magnet_link, title="Unknown"):
        gid = str(hash(magnet_link))[-8:]
        
        # webtorrent [magnet] -o [dir] --quiet
        # We don't use --quiet so we can potentially parse logs, 
        # but for now we'll just run it.
        cmd = ["npx", "-p", "webtorrent-cli", "webtorrent", "download", magnet_link, "-o", self.save_path]
        
        # Start in background
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.tasks[gid] = {
            "process": process,
            "title": title,
            "start_time": time.time(),
            "status": "active"
        }
        return gid

    def get_status(self):
        status_list = []
        for gid, t in list(self.tasks.items()):
            # Since webtorrent-cli is a separate process, we don't have easy RPC.
            # We'll just report it's running.
            poll = t['process'].poll()
            status = "active" if poll is None else "complete" if poll == 0 else "error"
            
            status_list.append({
                "gid": gid,
                "name": t['title'] + " (WebTorrent Mode)",
                "status": status,
                "progress": 50 if status == "active" else 100 if status == "complete" else 0,
                "download_speed": "WebTorrent Running..." if status == "active" else "Done",
                "total_length": "N/A",
                "completed_length": "N/A",
                "eta": "Calculating...",
                "num_peers": "Searching...",
                "is_metadata": False
            })
        return status_list

    def remove(self, gid):
        if gid in self.tasks:
            self.tasks[gid]['process'].terminate()
            del self.tasks[gid]
            return True
        return False
