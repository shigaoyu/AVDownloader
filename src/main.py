import sys
import yaml
import os
import argparse
from tqdm import tqdm
from scraper import JavScraper
from downloader import Aria2Downloader
from q_downloader import QBittorrentDownloader
from builtin_downloader import BuiltinDownloader

def _load_config(path="config/config.yaml"):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def select_best_magnet(magnets):
    if not magnets:
        return None
    
    # Priority: Subtitle (C) > Size
    def rank(m):
        score = 0
        name = m.get('name', '').lower()
        if 'c' in name or '字幕' in name or '-c' in name:
            score += 1000
        
        # Parse size (e.g. "6.52GB")
        size_str = m.get('size', '').lower()
        try:
            val = float(''.join(c for c in size_str if c.isdigit() or c == '.'))
            if 'gb' in size_str:
                score += val * 10
            elif 'mb' in size_str:
                score += val * 0.01
        except:
            pass
        return score

    return max(magnets, key=rank)

def search_code(code, scraper):
    print(f"\nSearching for {code}...")
    result = scraper.search(code)
    
    if not result:
        print(f"  [Error] No result found for {code}.")
        return None

    title = result.get('title', 'Unknown')
    best_magnet = select_best_magnet(result.get('magnets', []))
    
    if not best_magnet:
        print(f"  [Error] No magnets found for {title}.")
        return None

    print(f"  Found: {title}")
    print(f"  Magnet: {best_magnet['name']} ({best_magnet['size']})")
    
    return {
        "code": code,
        "title": title,
        "magnet": best_magnet['link']
    }

def main():
    parser = argparse.ArgumentParser(description="AV番号下载工具")
    parser.add_argument("codes", nargs="*", help="番号列表 (如 SSIS-123 SSNI-001)")
    parser.add_argument("-f", "--file", help="包含番号列表的文件")
    args = parser.parse_args()

    config = _load_config()
    codes = args.codes or []
    
    if args.file and os.path.exists(args.file):
        with open(args.file, 'r') as f:
            for line in f:
                code = line.strip()
                if code:
                    codes.append(code)

    if not codes:
        parser.print_help()
        return

    # Initialize Scraper
    scraper = JavScraper()
    
    # Initialize Downloader
    downloader_pref = config.get("downloader", "builtin")
    save_path = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(save_path):
        os.makedirs(save_path, exist_ok=True)

    downloader = None
    if downloader_pref == "builtin":
        downloader = BuiltinDownloader(save_path=save_path)
        if not downloader.check_connection():
            print("\n[ERROR] Download engine (aria2c) not found!")
            print("To fix this, please run: brew install aria2")
            print("-" * 50)
            return

    elif downloader_pref == "qbittorrent":
        qbt_conf = config.get("qbittorrent", {})
        downloader = QBittorrentDownloader(
            host=qbt_conf.get("host", "http://localhost"),
            port=qbt_conf.get("port", 8080),
            username=qbt_conf.get("username", "admin"),
            password=qbt_conf.get("password", "")
        )
        if not downloader.check_connection():
            print("\n[ERROR] qBittorrent Connection Failed. Please check if it is running.")
            return

    # Process Tasks
    results = []
    for code in codes:
        task = search_code(code, scraper)
        if not task:
            results.append({"code": code, "status": "Not Found"})
            continue

        # Start Download
        if isinstance(downloader, BuiltinDownloader):
            # Direct CLI download (blocking)
            success = downloader.download_sync(task['magnet'], title=task['title'])
            results.append({"code": code, "status": "Success" if success else "Failed/Interrupted"})
        else:
            # External RPC download (non-blocking)
            success = downloader.add_magnet(task['magnet'], save_path=save_path)
            results.append({"code": code, "status": "Pushed to Engine" if success else "Push Error"})

    # Final Summary
    print("\n" + "="*50)
    print(f"{'Code':<15} | {'Status':<30}")
    print("-"*50)
    for r in results:
        print(f"{r['code']:<15} | {r['status']:<30}")
    print("="*50)

if __name__ == "__main__":
    main()
