import re
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

from pytube import YouTube, Playlist

DOWNLOAD_DIR = os.path.join(os.getcwd(), "YTDLP")
DEBUG_FILE = 'DownloadList.txt'

proxy_set = input("Use proxy? (y/n): ").lower() in ["y", "yes", "yea", "ya", "yez", "yup", "ye"]
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

def download_video(url):
    try:
        print(f"Downloading with yt-dlp: {url}")
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            url,
            '-P', DOWNLOAD_DIR
        ]
        if proxy_set:
            cmd.extend(['--proxy', f"http://{proxy}"])
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp failed for {url}. Error: {e}")


def download_playlist(playlist_url):
    try:
        print(f"Downloading playlist with yt-dlp: {playlist_url}")
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            playlist_url,
            '-P', DOWNLOAD_DIR
        ]
        if proxy_set:
            cmd.extend(['--proxy', f"http://{proxy}"])
        subprocess.run(cmd, check=True)
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
    """Download videos from a list of URLs in a file."""
    count = 0
    try:
        with open(DEBUG_FILE, 'r') as f:
            urls = f.readlines()
        for url in urls:
            url = url.strip()
            if url:
                print(f"Downloading video {count + 1}: {url}")
                download_video(url)
                count += 1
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
        self.listbox = tk.Listbox(self, font=('Arial', 12))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
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
        download_video(url)
        self.load_downloaded_files()

    def threaded_download_playlist(self, url):
        download_playlist(url)
        self.load_downloaded_files()

    def load_downloaded_files(self):
        self.listbox.delete(0, tk.END)
        if os.path.exists(DOWNLOAD_DIR):
            for file in os.listdir(DOWNLOAD_DIR):
                self.listbox.insert(tk.END, os.path.join(DOWNLOAD_DIR, file))
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
