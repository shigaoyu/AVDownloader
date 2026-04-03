import libtorrent as lt
import time
import os
import threading
import json

class LTDownloader:
    """
    Pure Python downloader using libtorrent (pypi: libtorrent)
    More stable for magnet links on desktop than aria2 in some environments.
    """
    def __init__(self, save_path="./downloads"):
        self.save_path = os.path.abspath(save_path)
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        
        self.ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})
        self.handles = {} # gid -> handle

    def add_magnet(self, magnet_link, save_path=None):
        params = {
            'save_path': save_path or self.save_path,
            'storage_mode': lt.storage_mode_t(2),
        }
        handle = lt.add_magnet_uri(self.ses, magnet_link, params)
        gid = str(hash(magnet_link))[-8:]
        self.handles[gid] = handle
        return gid

    def get_status(self):
        status_list = []
        for gid, h in list(self.handles.items()):
            s = h.status()
            # state: 0=queued, 1=checking, 2=metadata, 3=downloading, 4=finished, 5=seeding
            state_map = ["waiting", "checking", "metadata", "active", "complete", "complete"]
            
            # If name is hash, it's still metadata
            name = h.name() if h.name() and not h.name().startswith('[') else "Searching Peers..."
            
            status_list.append({
                "gid": gid,
                "name": name,
                "status": state_map[s.state] if s.state < len(state_map) else "active",
                "progress": round(s.progress * 100, 1),
                "download_speed": f"{s.download_rate / 1024 / 1024:.2f} MB/s",
                "total_length": f"{s.total_wanted / 1024 / 1024 / 1024:.2f} GB" if s.total_wanted > 0 else "0 GB",
                "completed_length": f"{s.total_done / 1024 / 1024 / 1024:.2f} GB",
                "eta": f"{int((s.total_wanted - s.total_done) / s.download_rate)}s" if s.download_rate > 0 else "Inf",
                "num_peers": s.num_peers,
                "is_metadata": s.state <= 2
            })
        return status_list

    def remove(self, gid):
        if gid in self.handles:
            self.ses.remove_torrent(self.handles[gid])
            del self.handles[gid]
            return True
        return False

    def pause(self, gid):
        if gid in self.handles:
            self.handles[gid].pause()
            return True
        return False

    def resume(self, gid):
        if gid in self.handles:
            self.handles[gid].resume()
            return True
        return False
