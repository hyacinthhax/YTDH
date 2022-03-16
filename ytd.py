from pytube import YouTube
from pytube import Playlist
import os

'''Python 3 Script'''


def youtubedownload():
    exits = ['quit', 'exit', 'stop', 'q', 'leave']
    src = os.getcwd()
    menu = input(
        "Select 1 or 2 \n(1) One URL Download \n(2) Playlist Download \n(3) View Current Files \n<>")
    if menu == "":
        return youtubedownload()

    elif menu.lower() in exits:
        quit()

    elif int(menu) == 1:
        url = input('Please enter the URL:  ')
        print(f'Downloading {url} ... Please Wait... ')
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by(
            'resolution').desc().first()
        stream.download()
    elif int(menu) == 2:
        os.system('cls' if os.name == 'nt' else 'clear')
        url = input('Please enter playlist URL:  ')
        playlist_name = input("Please enter playlist Name:  ")
        playlist = Playlist(url)
        counts = len(playlist.video_urls)
        print(f"# of Videos: {counts}")
        dcounter = 0
        for video in playlist.videos:
            video.streams.get_highest_resolution().download(playlist_name)
            dcounter += 1
            print(f"Download Complete!  ({dcounter}/{counts})")
    elif int(menu) == 3:
        os.system('cls' if os.name == 'nt' else 'clear')
        for file in os.listdir(src):
            file_name, file_ext = os.path.splitext(file)
            if file_ext == '.mp4':
                print(f'Downloaded {file_name}  \n')
            else:
                pass

    else:
        print("Select 1-3!")
        return youtubedownload()


youtubedownload()
input('Enter To Continue... ')
os.system('cls' if os.name == 'nt' else 'clear')

while True:
    youtubedownload()

