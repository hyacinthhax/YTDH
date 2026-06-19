import re
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import queue

# Set current directory to script directory for resource loading
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

DOWNLOAD_DIR = os.path.join(os.getcwd(), "../YTDLP")
DEBUG_FILE = 'DownloadList.txt'

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def open_file(path):
    try:
        if os.name == 'nt':
            os.startfile(path)
        elif os.name == 'posix':
            subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', path])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open: {e}")

class YTDLPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp GUI")
        self.geometry("800x650")

        # GUI Settings Variables
        self.safety_var = tk.BooleanVar(value=True)
        self.proxy_set_var = tk.BooleanVar(value=False)
        self.proxy_var = tk.StringVar(value="")

        # Queue setup
        self.download_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.worker_thread.start()

        self.create_widgets()
        self.load_downloaded_files()
        self.log_message("System Ready. Waiting for tasks...")

    def create_widgets(self):
        # --- Top Search Bar Frame ---
        search_frame = tk.Frame(self)
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<Return>", self.load_downloaded_files)
        tk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT)

        # --- Listbox Frame ---
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame, font=('Arial', 12), yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<Double-1>", self.open_selected_file)
        self.listbox.bind("<Button-3>", self.right_click_delete)

        # --- Buttons Frame ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Download Video", command=self.popup_video).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Download Playlist", command=self.popup_playlist).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Download MP3", command=self.popup_mp3).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Playlist MP3", command=self.popup_playlist_mp3).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="From File", command=self.run_file_download).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Settings", command=self.open_settings).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_frame, text="Refresh", command=self.load_downloaded_files).pack(side=tk.LEFT, padx=3)

        # --- Terminal Output & Status Frame ---
        status_frame = tk.Frame(self)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.status_label = tk.Label(status_frame, text="Queue: 0 | Current: Idle", font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT)

        terminal_frame = tk.Frame(self)
        terminal_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        term_scroll = tk.Scrollbar(terminal_frame)
        term_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.terminal_box = tk.Text(terminal_frame, height=8, bg="black", fg="lightgreen", font=("Consolas", 9), yscrollcommand=term_scroll.set)
        self.terminal_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        term_scroll.config(command=self.terminal_box.yview)

    # --- UI Logging & Status Methods ---
    def log_message(self, message):
        """Safely print to the GUI terminal box from any thread."""
        self.after(0, self._insert_log, message)

    def _insert_log(self, message):
        self.terminal_box.insert(tk.END, message + "\n")
        self.terminal_box.see(tk.END) # Auto-scroll to bottom

    def update_status(self, text):
        """Safely update the fraction/status label."""
        self.after(0, lambda: self.status_label.config(text=text))

    def run_cmd_with_output(self, cmd):
        """Runs a subprocess and streams the output directly to the GUI terminal."""
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in process.stdout:
                clean_line = line.strip()
                if clean_line:
                    self.log_message(clean_line)
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
            return True
        except subprocess.CalledProcessError as e:
            self.log_message(f"ERROR: Command failed - {e}")
            return False

    # --- Worker Thread Logic ---
    def process_queue(self):
        """Worker thread to process downloads sequentially."""
        while True:
            self.update_status(f"Queue: {self.download_queue.qsize()} | Current: Idle")
            task = self.download_queue.get()
            action, url, safety, p_set, p_addr = task
            
            try:
                if action == "video":
                    self.download_video(url, safety, p_set, p_addr)
                elif action == "playlist":
                    self.download_playlist(url, safety, p_set, p_addr)
                elif action == "mp3":
                    self.download_mp3(url, p_set, p_addr)
                elif action == "playlist_mp3":
                    self.download_mp3_playlist(url, p_set, p_addr)
                elif action == "file":
                    self.download_from_file(safety, p_set, p_addr)
            except Exception as e:
                self.log_message(f"Critical error processing task: {e}")
            finally:
                self.after(0, self.load_downloaded_files)
                self.download_queue.task_done()
                self.log_message("--- Task Complete ---")

    # --- Download Methods ---
    def download_video(self, url, safety, proxy_set, proxy):
        self.log_message(f"\n[INIT] Downloading Video: {url}")
        self.update_status(f"Queue: {self.download_queue.qsize()} | Current: 1/1 (Video)")
        clean_url = url.split("&")[0]

        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            '--merge-output-format', 'mp4',
            '-P', DOWNLOAD_DIR, clean_url
        ]

        if safety:
            cmd.insert(1, '--match-filter')
            cmd.insert(2, 'availability = "public"')
        if proxy_set and proxy:
            cmd.extend(['--proxy', f"http://{proxy}"])

        self.run_cmd_with_output(cmd)

    def download_playlist(self, playlist_url, safety, proxy_set, proxy):
        self.log_message(f"\n[INIT] Scanning playlist: {playlist_url}")
        self.update_status(f"Queue: {self.download_queue.qsize()} | Current: Scanning Playlist...")

        cmd_list = ['yt-dlp', '--flat-playlist', '--print', 'https://www.youtube.com/watch?v=%(id)s', playlist_url]
        if proxy_set and proxy:
            cmd_list.extend(['--proxy', f"http://{proxy}"])
            
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        if result.returncode != 0:
            self.log_message("Failed to fetch playlist URLs.")
            return

        video_urls = result.stdout.strip().splitlines()
        total_videos = len(video_urls)
        self.log_message(f"Found {total_videos} videos in playlist.")

        for index, video_id in enumerate(video_urls, 1):
            full_url = video_id.strip()
            self.update_status(f"Queue: {self.download_queue.qsize()} | Current: {index}/{total_videos} (Playlist)")
            self.log_message(f"\n--- Processing [{index}/{total_videos}] ---")

            try:
                cmd_name = ['yt-dlp', '--get-filename', '-o', '%(title)s.%(ext)s', full_url]
                if proxy_set and proxy:
                    cmd_name.extend(['--proxy', f"http://{proxy}"])
                name_result = subprocess.run(cmd_name, capture_output=True, text=True)
                filename = name_result.stdout.strip()
                file_path = os.path.join(DOWNLOAD_DIR, filename)

                if os.path.exists(file_path):
                    self.log_message(f"Skipped (already downloaded): {filename}")
                    continue 
            except Exception:
                pass # Fail silently and just try downloading

            cmd_dl = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', 
                '--merge-output-format', 'mp4', full_url, '-P', DOWNLOAD_DIR
            ]
            if safety:
                cmd_dl.insert(1, '--match-filter')
                cmd_dl.insert(2, 'availability = "public"')
            if proxy_set and proxy:
                cmd_dl.extend(['--proxy', f"http://{proxy}"])
            
            self.run_cmd_with_output(cmd_dl)

    def download_mp3(self, url, proxy_set, proxy):
        self.log_message(f"\n[INIT] Downloading MP3: {url}")
        self.update_status(f"Queue: {self.download_queue.qsize()} | Current: 1/1 (MP3)")
        
        cmd = ['yt-dlp', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0', url]
        if proxy_set and proxy:
            cmd.extend(['--proxy', f"http://{proxy}"])
        self.run_cmd_with_output(cmd)

    def download_mp3_playlist(self, playlist_url, proxy_set, proxy):
        self.log_message(f"\n[INIT] Downloading Playlist MP3s: {playlist_url}")
        self.update_status(f"Queue: {self.download_queue.qsize()} | Current: Playlist MP3s")
        
        cmd = ['yt-dlp', '--extract-audio', '--audio-format', 'mp3', '--audio-quality', '0', playlist_url]
        if proxy_set and proxy:
            cmd.extend(['--proxy', f"http://{proxy}"])
        self.run_cmd_with_output(cmd)

    def download_from_file(self, safety, proxy_set, proxy):
        try:
            with open(DEBUG_FILE, 'r') as f:
                urls = [u.strip() for u in f.readlines() if u.strip()]
            
            total = len(urls)
            for index, url in enumerate(urls, 1):
                self.update_status(f"Queue: {self.download_queue.qsize()} | Current: {index}/{total} (File)")
                self.log_message(f"\n--- Processing File Line [{index}/{total}] ---")
                
                if 'playlist' in url or 'list=' in url:
                    self.download_playlist(url, safety, proxy_set, proxy)
                else:
                    self.download_video(url, safety, proxy_set, proxy)
        except FileNotFoundError:
            self.log_message(f"File not found: {DEBUG_FILE}")

    # --- GUI Inputs & Interaction ---
    def open_settings(self):
        settings_win = tk.Toplevel(self)
        settings_win.title("Download Settings")
        settings_win.geometry("300x150")
        settings_win.grab_set()

        tk.Checkbutton(settings_win, text="Safety Enabled (Public Only)", variable=self.safety_var).pack(pady=10, anchor='w', padx=20)
        proxy_frame = tk.Frame(settings_win)
        proxy_frame.pack(fill=tk.X, padx=20)
        tk.Checkbutton(proxy_frame, text="Use Proxy:", variable=self.proxy_set_var, command=self.toggle_proxy_entry).pack(side=tk.LEFT)
        self.proxy_entry = tk.Entry(proxy_frame, textvariable=self.proxy_var)
        self.proxy_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.toggle_proxy_entry()

    def toggle_proxy_entry(self):
        if hasattr(self, 'proxy_entry'):
            if self.proxy_set_var.get():
                self.proxy_entry.config(state=tk.NORMAL)
            else:
                self.proxy_entry.config(state=tk.DISABLED)

    def validate_and_enqueue(self, action, url=""):
        if self.proxy_set_var.get():
            proxy = self.proxy_var.get().strip()
            if not re.match(r'^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$', proxy):
                messagebox.showerror("Invalid Proxy", "Expected format: 127.0.0.1:8888")
                return

        self.download_queue.put((action, url, self.safety_var.get(), self.proxy_set_var.get(), self.proxy_var.get().strip()))
        self.update_status(f"Queue: {self.download_queue.qsize()} | Current: Active")
        self.log_message(f"Added {action} to queue.")

    def popup_video(self):
        url = simpledialog.askstring("Download Video", "Enter video URL:")
        if url: self.validate_and_enqueue("video", url)

    def popup_playlist(self):
        url = simpledialog.askstring("Download Playlist", "Enter playlist URL:")
        if url: self.validate_and_enqueue("playlist", url)

    def popup_mp3(self):
        url = simpledialog.askstring("Download MP3", "Enter video URL:")
        if url: self.validate_and_enqueue("mp3", url)

    def popup_playlist_mp3(self):
        url = simpledialog.askstring("Download Playlist MP3", "Enter playlist URL:")
        if url: self.validate_and_enqueue("playlist_mp3", url)

    def run_file_download(self):
        self.validate_and_enqueue("file")

    def clear_search(self):
        self.search_var.set("")
        self.load_downloaded_files()

    def load_downloaded_files(self, event=None):
        search_term = self.search_var.get().strip().lower()
        self.listbox.delete(0, tk.END)
        if os.path.exists(DOWNLOAD_DIR):
            for file in sorted(os.listdir(DOWNLOAD_DIR), key=lambda x: x.lower()):
                if not search_term or search_term in file.lower():
                    self.listbox.insert(tk.END, file)
        else:
            os.makedirs(DOWNLOAD_DIR)

    def right_click_delete(self, event):
        index = self.listbox.nearest(event.y)
        if index < 0: return
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        filename = self.listbox.get(index)
        
        if messagebox.askyesno("Delete File", f"Delete '{filename}'?"):
            try:
                os.remove(os.path.join(DOWNLOAD_DIR, filename))
                self.load_downloaded_files()
            except Exception as e:
                messagebox.showerror("Delete Failed", f"Could not delete file:\n{e}")

    def open_selected_file(self, event):
        selection = self.listbox.curselection()
        if selection:
            open_file(os.path.join(DOWNLOAD_DIR, self.listbox.get(selection[0])))

if __name__ == "__main__":
    clear_console()
    app = YTDLPApp()
    app.mainloop()