import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import queue
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import our core logic
from fourchan_downloader import FourChanScraper, FourChanDownloader

class FourChanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("4chan Batch Downloader")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        
        self.scraper = FourChanScraper()
        self.downloader = FourChanDownloader("downloads")
        self.threads = []
        self.msg_queue = queue.Queue()
        
        self._setup_styles()
        self._create_widgets()
        self._check_queue()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Subheader.TLabel", font=("Helvetica", 10, "italic"))

    def _create_widgets(self):
        # Main Container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_label = ttk.Label(main_frame, text="4chan Downloader", style="Header.TLabel")
        header_label.pack(pady=(0, 10))

        # Thread URL Input Section
        url_frame = ttk.LabelFrame(main_frame, text=" Thread URL ", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Thread URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.add_btn = ttk.Button(url_frame, text="Add Thread", command=self.add_thread)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        # Threads List Section
        threads_frame = ttk.LabelFrame(main_frame, text=" Threads to Download ", padding="10")
        threads_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Buttons for thread management
        btn_frame = ttk.Frame(threads_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.load_file_btn = ttk.Button(btn_frame, text="Load from File", command=self.load_from_file)
        self.load_file_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear All", command=self.clear_threads)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.remove_btn = ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected)
        self.remove_btn.pack(side=tk.LEFT, padx=5)
        
        # Listbox for threads
        self.thread_listbox = tk.Listbox(threads_frame, selectmode=tk.MULTIPLE, height=8)
        self.thread_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(threads_frame, orient=tk.VERTICAL, command=self.thread_listbox.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.thread_listbox.config(yscrollcommand=scrollbar.set)

        # Options Section
        options_frame = ttk.LabelFrame(main_frame, text=" Options ", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.use_original_names_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Use Original Filenames", variable=self.use_original_names_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(options_frame, text="Throttle (sec):").pack(side=tk.LEFT, padx=(20, 5))
        self.throttle_spin = ttk.Spinbox(options_frame, from_=0.1, to=5.0, increment=0.1, width=5)
        self.throttle_spin.set(0.5)
        self.throttle_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(options_frame, text="Max Workers:").pack(side=tk.LEFT, padx=(20, 5))
        self.workers_spin = ttk.Spinbox(options_frame, from_=1, to=10, increment=1, width=5)
        self.workers_spin.set(3)
        self.workers_spin.pack(side=tk.LEFT, padx=5)

        # Download Section
        dl_frame = ttk.Frame(main_frame)
        dl_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(dl_frame, text="🚀 Start Download", command=self.start_download)
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.gallery_btn = ttk.Button(dl_frame, text="🖼️ Generate Gallery", command=self.generate_gallery)
        self.gallery_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = ttk.Button(dl_frame, text="📁 Open Downloads", command=self.open_downloads)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)

        # Progress Section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        self.status_label = ttk.Label(progress_frame, text="Idle - Add thread URLs to start", style="Subheader.TLabel")
        self.status_label.pack(fill=tk.X)

        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text=" Logs ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        self.msg_queue.put(("log", message))

    def update_status(self, text):
        self.msg_queue.put(("status", text))

    def update_progress(self, val):
        self.msg_queue.put(("progress", val))

    def _check_queue(self):
        while not self.msg_queue.empty():
            msg_type, content = self.msg_queue.get()
            if msg_type == "log":
                self.log_area.insert(tk.END, content + "\n")
                self.log_area.see(tk.END)
            elif msg_type == "status":
                self.status_label.config(text=content)
            elif msg_type == "progress":
                self.progress_var.set(content)
            elif msg_type == "enable_btn":
                self.start_btn.config(state=tk.NORMAL)
            elif msg_type == "done":
                self.start_btn.config(state=tk.NORMAL)
                self.add_btn.config(state=tk.NORMAL)
                self.load_file_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Finished", "Download completed!")
        
        self.root.after(100, self._check_queue)

    def add_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Needed", "Please enter a thread URL.")
            return
        
        # Validate URL
        thread_info = self.scraper.parse_thread_url(url)
        if not thread_info:
            messagebox.showerror("Invalid URL", "Could not parse thread URL.\nFormat: https://boards.4chan.org/{board}/thread/{thread_id}")
            return
        
        # Check for duplicates
        for t in self.threads:
            if t['url'] == url:
                messagebox.showinfo("Duplicate", "This thread is already in the list.")
                return
        
        self.threads.append(thread_info)
        display_text = f"{thread_info['board']} / {thread_info['thread_id']}"
        if thread_info['thread_name'] != thread_info['thread_id']:
            display_text += f" ({thread_info['thread_name'][:30]})"
        self.thread_listbox.insert(tk.END, display_text)
        self.url_entry.delete(0, tk.END)
        self.log(f"Added thread: {display_text}")
        self.update_status(f"{len(self.threads)} thread(s) queued")

    def load_from_file(self):
        filename = filedialog.askopenfilename(
            title="Select file with thread URLs",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            added = 0
            skipped = 0
            for line in lines:
                url = line.strip()
                if not url or not url.startswith('http'):
                    continue
                
                # Check for duplicates
                if any(t['url'] == url for t in self.threads):
                    skipped += 1
                    continue
                
                thread_info = self.scraper.parse_thread_url(url)
                if thread_info:
                    self.threads.append(thread_info)
                    display_text = f"{thread_info['board']} / {thread_info['thread_id']}"
                    if thread_info['thread_name'] != thread_info['thread_id']:
                        display_text += f" ({thread_info['thread_name'][:30]})"
                    self.thread_listbox.insert(tk.END, display_text)
                    added += 1
            
            self.log(f"Loaded {added} thread(s) from file ({skipped} duplicates skipped)")
            self.update_status(f"{len(self.threads)} thread(s) queued")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def clear_threads(self):
        self.threads.clear()
        self.thread_listbox.delete(0, tk.END)
        self.update_status("No threads queued")
        self.log("Cleared all threads")

    def remove_selected(self):
        selected = self.thread_listbox.curselection()
        if not selected:
            return
        
        # Remove in reverse order to maintain indices
        for idx in reversed(selected):
            self.threads.pop(idx)
            self.thread_listbox.delete(idx)
        
        self.update_status(f"{len(self.threads)} thread(s) queued")
        self.log(f"Removed {len(selected)} thread(s)")

    def start_download(self):
        if not self.threads:
            messagebox.showwarning("No Threads", "Please add at least one thread URL.")
            return
        
        # Update downloader settings
        try:
            throttle = float(self.throttle_spin.get())
            max_workers = int(self.workers_spin.get())
            self.downloader.throttle = throttle
            self.downloader.max_workers = max_workers
        except ValueError:
            messagebox.showerror("Invalid Settings", "Please enter valid numbers for throttle and workers.")
            return
        
        self.start_btn.config(state=tk.DISABLED)
        self.add_btn.config(state=tk.DISABLED)
        self.load_file_btn.config(state=tk.DISABLED)
        self.log_area.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        use_original_names = self.use_original_names_var.get()
        total_threads = len(self.threads)
        
        for thread_idx, thread_info in enumerate(self.threads):
            board = thread_info['board']
            thread_id = thread_info['thread_id']
            thread_name = thread_info['thread_name']
            url = thread_info['url']
            
            self.update_status(f"[{thread_idx+1}/{total_threads}] Scraping {board}/{thread_id}...")
            self.log(f"Processing thread: {board}/{thread_id}")
            
            # Get thread info for better folder naming
            thread_meta = self.scraper.get_thread_info(url)
            if thread_meta.get('subject'):
                folder_name = thread_meta['subject'][:50]  # Limit length
            else:
                folder_name = thread_name
            
            # Scrape images
            images = self.scraper.scrape_thread_images(url)
            if isinstance(images, dict) and 'error' in images:
                self.log(f"  Error scraping: {images['error']}")
                continue
            
            if not images:
                self.log(f"  No images found in thread")
                continue
            
            self.log(f"  Found {len(images)} image(s)")
            
            # Get original filenames if requested
            original_names = None
            if use_original_names:
                original_names = self.scraper.get_image_titles(url)
            
            # Create folder
            folder = self.downloader.create_thread_folder(board, thread_id, folder_name)
            self.log(f"  Downloading to: {folder}")
            
            # Download images
            self._download_images(images, folder, use_original_names, original_names, thread_meta.get('subject'))
        
        self.update_status("All downloads finished.")
        self.msg_queue.put(("done", None))

    def _download_images(self, images, folder, use_original_names, original_names, thread_subject=None):
        total = len(images)
        done = 0
        
        with ThreadPoolExecutor(max_workers=self.downloader.max_workers) as executor:
            def download_task(args):
                idx, image_info = args
                orig_name = original_names[idx] if original_names and idx < len(original_names) else None
                return self.downloader.download_image(
                    image_info, folder, use_original_names, orig_name, 
                    thread_subject=thread_subject, save_metadata=True
                )

            futures = {executor.submit(download_task, (i, img)): i for i, img in enumerate(images)}
            for future in as_completed(futures):
                res = future.result()
                done += 1
                self.update_progress((done / total) * 100)
                
                if res['status'] == 'success':
                    self.log(f"    ✓ {res['filename']}")
                elif res['status'] == 'skipped':
                    self.log(f"    ⏭ {res['filename']} (exists)")
                elif res['status'] == 'failed':
                    self.log(f"    ✗ {res['filename']} - Error: {res.get('error')}")

    def open_downloads(self):
        import os
        folder = self.downloader.download_root
        if folder.exists():
            os.startfile(folder)
        else:
            messagebox.showinfo("No Downloads", "Downloads folder doesn't exist yet.")
    
    def generate_gallery(self):
        try:
            import gallery_generator
            gallery_path = gallery_generator.generate_gallery(self.downloader.download_root, "4chan Downloads")
            messagebox.showinfo("Gallery Generated", f"Gallery generated at:\n{gallery_path}")
            import os
            os.startfile(gallery_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate gallery: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FourChanGUI(root)
    root.mainloop()
