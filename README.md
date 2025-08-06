# yt-dlp tool

以下是适用于你的 PyQt5 视频下载 GUI 工具的 GitHub 项目 `README.md` 模板：

---

## 🎬 YT-DLP GUI 视频下载器（基于 PyQt5）

一个基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的桌面图形界面工具，使用 PyQt5 开发，支持音视频下载、进度显示、Cookie 登录与配置保存。

![screenshot](https://your-screenshot-url.com/)

---

### ✅ 功能特点

- 🔊 支持下载：**仅音频** / **仅视频** / **音视频合成**

- 📂 自定义保存路径 & 文件命名

- 🍪 支持 Cookie 登录（适用于会员/登录内容）

- 💾 自动保存与加载配置

- 📊 实时显示下载日志与进度条

- ⚙️ 可调节下载线程数（1-64线程滑动条）

---

### 📦 环境依赖

- Python 3.7+

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

- PyQt5

安装依赖：

```bash
pip install pyqt5
```

---

### 🚀 使用方法

1. **下载 yt-dlp 可执行文件**
   
   下载main.py

2. **运行程序**

```bash
python main.py
```

3. **填写下载信息**
- yt-dlp 路径：填写 `yt-dlp.exe` 路径

- 视频 URL：粘贴要下载的视频链接

- 保存路径：选择输出目录

- 可选 Cookie 文件（用于登录下载）
4. **点击「开始下载」按钮**
- 显示完整命令和执行过程

- 下载成功后会弹出提示框

- 进度条动态更新

---

### 🧠 进阶用法

- 支持 `cookie.txt` 登录（如 Pixiv FANBOX、Bilibili 等）

- 支持 MP3 音频提取 (`-x --audio-format mp3`)

- 支持配置持久化（点击“保存配置”按钮）

---

### 📝 配置文件

配置默认保存在本地的 `ytdlp_config.ini`，包含以下字段：

```ini
[Settings]
ytdlp_path=D:/yt-dlp.exe
output_path=D:/Downloads
cookie_path=D:/cookie.txt
download_type=全部合成
use_cookie=True
thread_count=4
```

---

### 🔧 TODO（建议功能）

- 支持多任务下载队列

- 下载完成后自动打开文件夹

- 国际化支持（中/英切换）

---

### 📄 License

MIT License © 2025

---
