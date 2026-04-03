from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import threading
import json
import aria2p
import yaml
import httpx
import subprocess
from scraper import JavScraper
import time

# Utility: Fetch latest trackers to boost download speed
def get_best_trackers():
    try:
        # High quality trackers from popular lists
        urls = [
            "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt",
            "https://newtrackon.com/api/stable"
        ]
        all_trackers = []
        with httpx.Client(timeout=5.0) as client:
            for url in urls:
                try:
                    r = client.get(url)
                    if r.status_code == 200:
                        all_trackers.extend([line.strip() for line in r.text.split("\n") if line.strip()])
                except: continue
        return ",".join(list(set(all_trackers)))
    except:
        return ""

# Inject trackers into downloaders
def boost_downloader():
    trackers = get_best_trackers()
    if not trackers: return
    
    # Boost Aria2
    try:
        aria2.set_global_options({"bt-tracker": trackers})
        print("Aria2 boosted with new trackers.")
    except: pass
    
    # Boost Transmission
    try:
        # For Transmission, we add trackers to each torrent via tr_engine or CLI
        pass
    except: pass

# NEW: Transmission Engine for stable Mac magnet downloads
from tr_downloader import TransmissionDownloader
tr_engine = TransmissionDownloader(save_path=os.path.abspath("downloads"))

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Load config
def load_config():
    path = "config/config.yaml"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

config = load_config()
scraper = JavScraper()

# Image Proxy
@app.route('/api/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url: return "No URL", 400
    proxy = config.get("proxy")
    try:
        with httpx.Client(proxy=proxy if proxy else None, follow_redirects=True, timeout=10.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.javbus.com/" if "javbus" in url else "https://javdb.com/"
            }
            resp = client.get(url, headers=headers)
            return resp.content, resp.status_code, {"Content-Type": resp.headers.get("Content-Type", "image/jpeg")}
    except Exception as e:
        return str(e), 500

# Initialize Aria2 Client (Legacy)
aria2_client = aria2p.Client(
    host=config.get("aria2", {}).get("host", "http://127.0.0.1"),
    port=config.get("aria2", {}).get("port", 6800),
    secret=config.get("aria2", {}).get("secret", "")
)
aria2 = aria2p.API(aria2_client)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    code = data.get('code', '').strip()
    if not code: return jsonify({"error": "No code provided"}), 400
    result = scraper.search(code)
    if not result: return jsonify({"error": "Not found"}), 404
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    magnet = data.get('magnet')
    title = data.get('title', 'Unknown')
    
    if not magnet: return jsonify({"error": "No magnet link provided"}), 400

    save_path = os.path.abspath("downloads")
    if not os.path.exists(save_path): os.makedirs(save_path, exist_ok=True)

    try:
        # Use Transmission (The Stable Engine)
        gid = tr_engine.add_magnet(magnet, title=title)
        if gid:
            return jsonify({"status": "success", "gid": gid, "title": title, "engine": "transmission"})
        else:
            # Fallback to Aria2 if transmission fails
            options = {"dir": save_path}
            download_task = aria2.add_magnet(magnet, options=options)
            return jsonify({"status": "success", "gid": download_task.gid, "title": title, "engine": "aria2"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    combined_status = []
    # 1. Get Transmission status
    try:
        combined_status.extend(tr_engine.get_status())
    except: pass
    
    # 2. Get Aria2 status (Fallback)
    try:
        downloads = aria2.get_downloads()
        for d in downloads:
            name = d.name if d.name else "Aria2: Searching..."
            combined_status.append({
                "gid": d.gid,
                "name": name,
                "status": d.status,
                "progress": d.progress,
                "download_speed": d.download_speed_string(),
                "total_length": d.total_length_string(),
                "completed_length": d.completed_length_string(),
                "eta": d.eta_string(),
                "num_peers": d.connections,
                "is_metadata": not d.name or d.name.startswith('[METADATA]')
            })
    except: pass
            
    return jsonify(combined_status)

@app.route('/api/task/remove', methods=['POST'])
def remove_task():
    data = request.json
    gid = data.get('gid')
    try:
        if tr_engine.remove(gid): return jsonify({"status": "success"})
        aria2.remove([aria2.get_download(gid)], force=True, files=True)
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

@app.route('/api/task/pause', methods=['POST'])
def pause_task():
    data = request.json
    gid = data.get('gid')
    try:
        if tr_engine.pause(gid): return jsonify({"status": "success"})
        aria2.pause([aria2.get_download(gid)])
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

@app.route('/api/task/resume', methods=['POST'])
def resume_task():
    data = request.json
    gid = data.get('gid')
    try:
        if tr_engine.resume(gid): return jsonify({"status": "success"})
        aria2.resume([aria2.get_download(gid)])
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

if __name__ == '__main__':
    print("Web UI started at http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
