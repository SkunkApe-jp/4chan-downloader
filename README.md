# 4chan Batch Downloader & Gallery

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, high-performance 4chan media downloader with a clean GUI and rich metadata support. Move beyond simple script-based downloading and enjoy a premium interface for collecting and viewing your favorite boards.

---

## ✨ Key Features

- 🖥️ **Modern Desktop GUI**: A user-friendly Tkinter-based interface for managing thread queues and download status.
- 🚀 **Multi-threaded Performance**: Lightning-fast image scraping and downloading using concurrent execution.
- 📊 **Rich Metadata Support**: Every downloaded file is accompanied by a `.json` metadata file containing uploader name, post number, timestamps, and uploader-specified filename.
- 🖼️ **Dynamic HTML Gallery**: Automatically generate professional-looking galleries with search functionality, tag filtering, and built-in video player.
- 📁 **Smart Folder Organization**: Downloads are sorted by board title, thread ID, and subject for easy navigation.
- ⚙️ **Customizable Settings**: Control download throttle, thread count, and filename preservation (ID vs Original).

---

## 🛠️ Getting Started

### Installation & Build
For the best experience, the application should be built into a standalone executable:

1.  **Clone & Prepare**:
    ```bash
    git clone https://github.com/SkunkApe-jp/4chan-downloader.git
    cd 4chan-downloader
    pip install -r requirements.txt
    ```
2.  **Build the Standalone**:
    ```bash
    python build_exe.py
    ```
3.  **Run the App**: Launch `dist/FourChanDownloader.exe` to get started.

### Source Usage
If you prefer running the source directly for development:
```bash
python gui.py
```

While you can run the source directly with `python gui.py`, **it is highly recommended to build a standalone executable** for the best performance and simplified experience:

1.  **Build the Executable**:
    ```bash
    python build_exe.py
    ```
2.  **Run the App**: Once finished, you'll find `FourChanDownloader.exe` inside the `dist/` folder. This is the preferred way to run the downloader as it bundles all dependencies into a single, optimized file.

From the GUI, simply paste thread URLs and start the download. Once finished, click **"Generate Gallery"** to create an interactive browser-based view of your collection.

---

## 🏗️ Project Architecture

The project has been modernized into a clean, modular structure:

| File | Purpose |
| :--- | :--- |
| `gui.py` | **Main Entry Point**. The desktop application interface. |
| `fourchan_downloader.py` | Core scraping and downloading library (replaces legacy script logic). |
| `gallery_generator.py` | Generates a high-end HTML/JS gallery inside download folders. |
| `thread-watcher.py` | Advanced utility for monitoring boards for specific keywords. |
| `inb4404.py` | **Legacy CLI Script** (kept for backward compatibility). |

---

## 🖼️ Premium Gallery Features

- **Instant Search**: Find specific images by filename, board, or poster name instantly.
- **Tag Filtering**: Filter the collection by uploader or board with dynamic tag clouds.
- **Media Viewer**: Full-screen modal support for viewing high-res images and autoplaying WebMs/MP4s.
- **Dark Mode**: Optimized for viewing at night with a sleek, minimalist dark theme.

## 🗒️ Notes & Tips

- **Original Filenames**: If enabled, invalid filesystem characters are automatically sanitized to ensure compatibility across OSes.
- **Rate Management**: Adjust the "Throttle" in the GUI to avoid triggering 4chan's rate limiting (recommended: `0.5s` - `1.0s`).
- **Batch Processing**: You can load a text file containing multiple URLs directly into the GUI queue.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.

> [!NOTE]
> This project is a modern fork designed to streamline media collection and archiving from 4chan boards while preserving the original content's context.
