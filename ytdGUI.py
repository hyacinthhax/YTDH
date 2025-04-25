import re
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

from pytube import YouTube, Playlist

choices_yes = ["y", "yes", "yea", "ya", "yez", "yup", "ye", "yeah"]
DOWNLOAD_DIR = os.path.join(os.getcwd(), "YTDLP")
DEBUG_FILE = 'DownloadList.txt'
safety = input("Download with Safety?(Public Only): ").lower() in choices_yes
proxy_set = input("Use proxy? (y/n): ").lower() in choices_yes
proxy_re = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$')
if proxy_set:
    proxy = input("Enter proxy (e.g., 127.0.0.1:8888):  ")
    if not proxy_re.match(proxy):
        print("Invalid proxy format. Expected format: 127.0.0.1:8888")
        sys.exit(1)
    os.environ['http_proxy'] = f"http://{proxy}/"
    os.environ['https_proxy'] = f"http://{proxy}/"

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

def download_video(url, safety=True):
    try:
        print(f"Downloading with yt-dlp: {url}")
        cmd = ['yt-dlp', '--get-filename', '-o', '%(title)s.%(ext)s', url]
        if proxy_set:
            cmd.extend(['--proxy', f"http://{proxy}"])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        filename = result.stdout.strip()
        file_path = os.path.join(DOWNLOAD_DIR, filename)

        if os.path.exists(file_path):
            print(f"Already downloaded: {filename}")
            pass

        if not safety:
            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                url,
                '-P', DOWNLOAD_DIR
            ]

        if safety:
            cmd = [
                'yt-dlp',
                '--match-filter', 'availability = "public"',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                url,
                '-P', DOWNLOAD_DIR
            ]

        if proxy_set:
            cmd.extend(['--proxy', f"http://{proxy}"])
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp failed for {url}. Error: {e}")


def download_playlist(playlist_url, safety=True):
    try:
        print(f"Scanning playlist: {playlist_url}")

        # Step 1: Get video URLs from the playlist
        cmd_list = ['yt-dlp', '--flat-playlist', '--print', '%(url)s', playlist_url]
        if proxy_set:
            cmd_list.extend(['--proxy', f"http://{proxy}"])
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        video_urls = result.stdout.strip().splitlines()

        for index, video_id in enumerate(video_urls, 1):
            full_url = video_id.strip()
            print(f"  [{index}/{len(video_urls)}] Checking {full_url}")

            # Step 2: Predict filename
            try:
                cmd_name = ['yt-dlp', '--get-filename', '-o', '%(title)s.%(ext)s', full_url]
                if proxy_set:
                    cmd_name.extend(['--proxy', f"http://{proxy}"])
                name_result = subprocess.run(cmd_name, capture_output=True, text=True, check=True)
                filename = name_result.stdout.strip()
                file_path = filename

                if os.path.exists(file_path):
                    print(f"    Skipped (already downloaded): {filename}")
                    continue
            except subprocess.CalledProcessError as e:
                print(f"    Failed to get filename for {full_url}. Error: {e}")
                continue

            # Step 3: Download the video
            print(f"    Downloading: {full_url}")
            if not safety:
                cmd_dl = [
                    'yt-dlp',
                    '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    full_url,
                    '-P', DOWNLOAD_DIR
                ]
            if safety:
                cmd_dl = [
                    'yt-dlp',
                    '--match-filter', 'availability = "public"',
                    '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    full_url,
                    '-P', DOWNLOAD_DIR
                ]

            if proxy_set:
                cmd_dl.extend(['--proxy', f"http://{proxy}"])
            subprocess.run(cmd_dl, check=True)

    except subprocess.CalledProcessError as e:
        print(f"yt-dlp playlist failed. Error: {e}")

def mp3_download(url):
    try:
        print(f"Downloading mp3 with yt-dlp: {url}")
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            url
        ]
        if proxy_set:
            cmd.extend(['--proxy', f"http://{proxy}"])
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp failed for {url}. Error: {e}")


def mp3_playllist_download(playlist_url):
    try:
        print(f"Downloading playlist with yt-dlp: {playlist_url}")
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            playlist_url
        ]
        if proxy_set:
            cmd.extend(['--proxy', f"http://{proxy}"])
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp playlist failed. Error: {e}")


def download_from_file():
    """Download videos and playlists from a list of URLs in a file."""
    count = 0
    try:
        with open(DEBUG_FILE, 'r') as f:
            urls = f.readlines()
        for url in urls:
            url = url.strip()
            if url:
                count += 1
                print(f"Processing {count}: {url}")
                # Naively assume it's a playlist if it contains 'playlist' or 'list='
                if 'playlist' in url or 'list=' in url:
                    download_playlist(url, safety)
                else:
                    download_video(url, safety)
        print("File download complete.")
    except FileNotFoundError:
        print(f"File not found: {DEBUG_FILE}")
    except Exception as e:
        print(f"Error during file download: {e}")


class YTDLPApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp GUI (with pytube)")
        self.geometry("720x480")

        self.create_widgets()
        self.load_downloaded_files()

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(frame, font=('Arial', 12), yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<Double-1>", self.open_selected_file)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Download Video", command=self.popup_video).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Download Playlist", command=self.popup_playlist).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Download MP3", command=self.popup_mp3).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Playlist MP3", command=self.popup_playlist_mp3).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="From File", command=self.run_file_download).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_downloaded_files).pack(side=tk.LEFT, padx=5)

    def popup_mp3(self):
        url = simpledialog.askstring("Download Video", "Enter video URL:")
        if url:
            threading.Thread(target=self.threaded_download_video, args=(url,), daemon=True).start()

    def popup_playlist_mp3(self):
        url = simpledialog.askstring("Download Playlist", "Enter playlist URL:")
        if url:
            threading.Thread(target=self.threaded_download_playlist, args=(url,), daemon=True).start()

    def popup_video(self):
        url = simpledialog.askstring("Download Video", "Enter video URL:")
        if url:
            threading.Thread(target=self.threaded_download_video, args=(url,), daemon=True).start()

    def popup_playlist(self):
        url = simpledialog.askstring("Download Playlist", "Enter playlist URL:")
        if url:
            threading.Thread(target=self.threaded_download_playlist, args=(url,), daemon=True).start()

    def run_file_download(self):
        threading.Thread(target=download_from_file, daemon=True).start()

    def threaded_download_video(self, url):
        download_video(url, safety)
        self.load_downloaded_files()

    def threaded_download_playlist(self, url):
        download_playlist(url, safety)
        self.load_downloaded_files()

    def load_downloaded_files(self):
        self.listbox.delete(0, tk.END)
        if os.path.exists(DOWNLOAD_DIR):
            files = sorted(os.listdir(DOWNLOAD_DIR), key=lambda x: x.lower())
            for file in files:
                self.listbox.insert(tk.END, file)
        else:
            os.makedirs(DOWNLOAD_DIR)


    def open_selected_file(self, event):
        selection = self.listbox.curselection()
        if selection:
            file_path = self.listbox.get(selection[0])
            open_file(file_path)


if __name__ == "__main__":
    clear_console()
    app = YTDLPApp()
    app.mainloop()
