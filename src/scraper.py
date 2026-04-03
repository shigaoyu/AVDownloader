import httpx
from bs4 import BeautifulSoup
import yaml
import os
import re
import random

class JavScraper:
    def __init__(self, config_path="config/config.yaml"):
        self.config = self._load_config(config_path)
        proxy = self.config.get("proxy")
        
        self.client = httpx.Client(
            proxy=proxy if proxy else None, 
            follow_redirects=True, 
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            cookies={"existmag": "all"}
        )

    def _load_config(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def search(self, code):
        result = self.search_javbus(code)
        if not result or not result.get("magnets"):
            # If JAVBus fails or has no magnets, try JAVDB
            result_javdb = self.search_javdb(code)
            if result_javdb:
                return result_javdb
        return result

    def search_javbus(self, code):
        url = f"https://www.javbus.com/{code.upper()}"
        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            title_elem = soup.select_one("h3")
            if not title_elem: return None
            title = title_elem.text.strip()
            
            cover_elem = soup.select_one(".bigImage img")
            cover = cover_elem['src'] if cover_elem else ""
            if cover and not cover.startswith("http"):
                cover = "https://www.javbus.com" + (cover if cover.startswith("/") else "/" + cover)
            
            magnets = []
            script_text = "".join([s.text for s in soup.find_all("script")])
            gid_match = re.search(r"var gid = (\d+);", script_text)
            uc_match = re.search(r"var uc = (\d+);", script_text)
            img_match = re.search(r"var img = '(.+?)';", script_text)

            if gid_match:
                gid = gid_match.group(1)
                uc = uc_match.group(1) if uc_match else "0"
                img = img_match.group(1) if img_match else ""
                floor = random.randint(1, 1000)
                
                # New AJAX URL pattern found
                ajax_url = f"https://www.javbus.com/ajax/uncledatoolsbyajax.php?gid={gid}&lang=zh&img={img}&uc={uc}&floor={floor}"
                
                ajax_resp = self.client.get(ajax_url, headers={"Referer": url, "X-Requested-With": "XMLHttpRequest"})
                if ajax_resp.status_code == 200:
                    ajax_soup = BeautifulSoup(ajax_resp.text, 'html.parser')
                    rows = ajax_soup.select("tr")
                    for row in rows:
                        tds = row.select("td")
                        if len(tds) < 3: continue
                        
                        link_elem = tds[0].select_one("a")
                        if not link_elem: continue
                        
                        name = link_elem.text.strip()
                        link = link_elem['href']
                        size = tds[1].text.strip()
                        date = tds[2].text.strip()
                        
                        magnets.append({
                            "name": name,
                            "link": link,
                            "size": size,
                            "date": date
                        })
            
            return {
                "title": title,
                "cover": cover,
                "magnets": magnets,
                "source": "javbus"
            }
        except Exception as e:
            print(f"JAVBus error for {code}: {e}")
            return None

    def search_javdb(self, code):
        url = f"https://javdb.com/search?q={code}&f=all"
        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            item = soup.select_one(".grid-item a")
            if not item:
                return None
            
            movie_url = "https://javdb.com" + item['href']
            return self.get_movie_details_javdb(movie_url)
        except Exception as e:
            return None

    def get_movie_details_javdb(self, url):
        try:
            resp = self.client.get(url)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.select_one(".title strong").text.strip()
            cover_elem = soup.select_one(".video-cover")
            cover = cover_elem['src'] if cover_elem else ""
            
            magnets = []
            magnet_items = soup.select("#magnet-links .item")
            for item in magnet_items:
                name_elem = item.select_one(".name")
                if not name_elem: continue
                
                name = name_elem.text.strip()
                link = item.select_one("a")['href']
                size = item.select_one(".meta").text.strip()
                
                magnets.append({
                    "name": name,
                    "link": link,
                    "size": size
                })
                
            return {
                "title": title,
                "cover": cover,
                "magnets": magnets,
                "source": "javdb"
            }
        except Exception as e:
            return None
