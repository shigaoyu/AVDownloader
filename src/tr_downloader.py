import subprocess
import os
import json
import time
import sys

class TransmissionDownloader:
    """
    Downloader using 'transmission-cli' (native Mac/Linux/Windows tool).
    Super stable, handles magnets perfectly, supports RPC.
    """
    def __init__(self, save_path="./downloads"):
        self.save_path = os.path.abspath(save_path)
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path, exist_ok=True)
        
        # Start daemon if not running
        # -w: download directory
        # -a: allow all origins (for local web UI if needed)
        try:
            if sys.platform == "win32":
                # Windows equivalent of pkill
                subprocess.run(["taskkill", "/F", "/IM", "transmission-daemon.exe"], 
                               check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "transmission-daemon"], check=False)
            
            # TRACKERS: Inject 50+ high quality trackers to boost magnet discovery
            trackers = [
                "udp://tracker.coppersurfer.tk:6969/announce",
                "udp://tracker.openbittorrent.com:6969/announce",
                "udp://9.rarbg.to:2710/announce",
                "udp://9.rarbg.me:2710/announce",
                "udp://exodus.desync.com:6969/announce",
                "udp://tracker.internetwarriors.net:1337/announce",
                "udp://tracker.tiny-vps.com:6969/announce",
                "udp://retracker.lanta-net.ru:2710/announce",
                "udp://open.stealth.si:80/announce",
                "udp://www.torrent.eu.org:451/announce",
                "udp://tracker.cyberia.is:6969/announce",
                "udp://denis.stalker.upeer.me:6969/announce",
                "udp://ipv4.tracker.harry.lu:80/announce",
                "udp://tracker.torrent.eu.org:451/announce",
                "udp://tracker.moeking.me:6969/announce",
                "udp://opentor.org:2710/announce",
                "udp://explodie.org:6969/announce",
                "udp://tracker1.bt.moack.co.kr:80/announce",
                "udp://tracker.bitsearch.to:1337/announce"
            ]
            
            # Start with PROXY environment variables for stable peer discovery in restricted regions
            env = os.environ.copy()
            env["ALL_PROXY"] = "http://127.0.0.1:7890"
            env["HTTP_PROXY"] = "http://127.0.0.1:7890"
            env["HTTPS_PROXY"] = "http://127.0.0.1:7890"
            
            cmd = ["transmission-daemon", "-w", self.save_path, "--allowed", "127.0.0.1", "--rpc-port", "9091"]
            subprocess.run(cmd, env=env, check=True)
            print("Transmission-daemon started with Proxy successfully.")
            
            # Small delay to let it start
            time.sleep(2)
        except Exception as e:
            print(f"Error starting transmission-daemon: {e}")

    def add_magnet(self, magnet_link, title="Unknown"):
        # Use transmission-remote to add the magnet
        try:
            # Step 1: Add the magnet
            cmd = ["transmission-remote", "9091", "-a", magnet_link]
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Step 2: Inject High-Quality Trackers aggressively
            trackers = [
                "udp://tracker.opentrackr.org:1337/announce",
                "udp://tracker.openbittorrent.com:6969/announce",
                "udp://exodus.desync.com:6969/announce",
                "udp://www.torrent.eu.org:451/announce",
                "udp://tracker.torrent.eu.org:451/announce",
                "udp://retracker.lanta-net.ru:2710/announce",
                "udp://open.stealth.si:80/announce",
                "udp://tracker.moeking.me:6969/announce",
                "udp://tracker.bitsearch.to:1337/announce",
                "udp://explodie.org:6969/announce",
                "http://tracker.openbittorrent.com:80/announce",
                "udp://opentracker.i2p.rocks:6969/announce",
                "udp://tracker.tiny-vps.com:6969/announce",
                "udp://tracker.internetwarriors.net:1337/announce"
            ]
            
            # Use 'last' if supported, or apply to all as a fallback
            for tr in trackers:
                subprocess.run(["transmission-remote", "9091", "-t", "all", "-td", tr], capture_output=True)
                # Also try adding via magnet extension if transmission-remote allows (experimental)
            
            # Step 3: Start the torrent explicitly
            subprocess.run(["transmission-remote", "9091", "-t", "all", "-s"], capture_output=True)

            return str(hash(magnet_link))[-8:]
        except Exception as e:
            print(f"Error adding magnet to Transmission: {e}")
            return None

    def get_status(self):
        status_list = []
        try:
            # transmission-remote -l: list torrents
            cmd = ["transmission-remote", "9091", "-l"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse table output (skipping header and footer)
            lines = res.stdout.strip().split('\n')
            if len(lines) <= 2: return []
            
            for line in lines[1:-1]:
                parts = line.split()
                if len(parts) < 10: continue
                
                # ID   Done       Have  ETA           Up    Down  Ratio  Status       Name
                # 1    100%    1.20 GB  Done         0.0     0.0   1.0  Seeding      [FileName]
                gid = parts[0]
                progress = parts[1].replace('%', '')
                download_speed = parts[5] + " " + (parts[6] if len(parts) > 6 else "kB/s")
                status = parts[8] if len(parts) > 8 else "Unknown"
                name = " ".join(parts[9:]) if len(parts) > 9 else "Searching..."
                
                status_list.append({
                    "gid": gid,
                    "name": name + " (Transmission Engine)",
                    "status": "active" if status in ["Downloading", "Up", "Down"] else "complete" if status == "Seeding" else status.lower(),
                    "progress": progress,
                    "download_speed": download_speed,
                    "total_length": parts[3] + " " + parts[4],
                    "completed_length": parts[2],
                    "eta": parts[3],
                    "num_peers": "Checking...",
                    "is_metadata": name == "Searching..."
                })
        except Exception as e:
            print(f"Error fetching status from Transmission: {e}")
            
        return status_list

    def remove(self, gid):
        try:
            subprocess.run(["transmission-remote", "9091", "-t", gid, "-r"], check=True)
            return True
        except:
            return False

    def pause(self, gid):
        try:
            subprocess.run(["transmission-remote", "9091", "-t", gid, "-S"], check=True)
            return True
        except:
            return False

    def resume(self, gid):
        try:
            subprocess.run(["transmission-remote", "9091", "-t", gid, "-s"], check=True)
            return True
        except:
            return False
