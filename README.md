# AV Downloader Pro (番号极速云下载)

一个专为 macOS/Windows 设计的现代化、自动化番号下载管理系统。集成强大的爬虫引擎与多重下载方案，提供极致的 Web 管理体验。

---

## 🚀 核心特性 (Features)

- **现代化卡片式 Web UI**：基于 Bootstrap 5 & Inter 字体设计的紧凑型管理后台，支持深色模式视觉风格。
- **智能爬虫引擎**：实时抓取 JAVBus / JAVDB 数据库，自动识别封面图、发行日期及磁力节点。
- **双引擎驱动 (Dual-Engine)**：
  - **Aria2 PRO**：内置 SOCKS5 代理优化与 UPnP 穿透，适合后台静默下载。
  - **Transmission**：作为 macOS 环境下的高稳定性备份引擎。
- **极速磁力加速**：自动注入 50+ 全球顶级 Tracker 服务器，大幅提升磁力链接的 Peer 发现速度。
- **智能筛选算法**：默认优先级：**带中文字幕 (-C/字幕)** > **资源文件体积（高清优先）**。
- **云下载 + 本地唤起 (Hybrid Mode)**：
  - **云下载**：直接在 Web 界面一键建立下载任务，后台全自动处理。
  - **外部打开**：如果内置引擎受限，可一键拉起本地专业下载器（qBittorrent / BitComet 等）。

---

## 🛠️ 技术架构 (Tech Stack)

- **Backend**: Python 3.12 + Flask
- **Frontend**: Bootstrap 5 + Bootstrap Icons + Animate.css
- **Engines**: Aria2 (RPC) / Transmission (Daemon)
- **Scraper**: BeautifulSoup4 + httpx (支持代理隧道)
- **Configuration**: YAML / JSON

---

## ⚙️ 快速开始 (Quick Start)

### 1. 安装环境依赖
```bash
# 克隆项目并安装 Python 库
pip3 install flask flask-cors httpx beautifulsoup4 pyyaml aria2p
```

### 2. 安装下载核心 (macOS 推荐)
```bash
brew install aria2 transmission-cli
```

### 3. 配置代理与路径
编辑 `config/config.yaml`：
- `proxy`: 配置你的本地代理（如 `http://127.0.0.1:7890`）以访问元数据服务器。
- `save_path`: 设定你的视频保存目录。

### 4. 启动服务
```bash
# 启动 Web 服务 (默认端口 5001)
python3 src/app.py
```
访问浏览器： [http://127.0.0.1:5001](http://127.0.0.1:5001) 即可开始。

---

## ⚠️ 重要说明 (Disclaimer)

### 关于“云下载”功能 (Aria2/Transmission)
**由于 P2P 下载受本地网络环境（运营商封锁、公网 IP、防火墙）影响巨大，界面中的“云下载”功能可能无法在所有环境下达到理想速度：**

1. **Searching Metadata**：磁力链接在解析初期需要寻找 Peer，如果 2 分钟后仍未显示文件名，说明该种子在当前网络下无法握手。
2. **下载速度为 0**：如果出现任务建立了但无速度的情况，通常是由于缺乏活跃种子或 Tracker 被屏蔽。
3. **推荐方案**：如果云下载无法工作，**请优先点击磁力旁边的“外部打开”按钮**。这将直接唤起你本地安装的专业下载软件（如迅雷、qBittorrent），利用它们更强大的穿透能力和离线加速服务。

---

## 🔧 端口占用说明
- **Web UI**: `5001` (避开了 macOS 5000 端口占用)
- **Aria2 RPC**: `6800`
- **Transmission RPC**: `9091`

---

## 📁 目录结构
```text
.
├── config/              # 系统配置文件
├── src/
│   ├── app.py           # Flask 后端核心
│   ├── scraper.py       # JAV 爬虫逻辑
│   ├── downloader.py    # Aria2 调度引擎
│   └── tr_downloader.py # Transmission 调度引擎
├── templates/           # 精致 Web UI 前端模板
├── downloads/           # 视频默认下载目录
├── aria2.conf           # Aria2 PRO 优化配置
└── app.log              # 系统运行日志
```

---
*Created with ❤️ for high-performance downloading experience.*
