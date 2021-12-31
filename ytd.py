from pytube import YouTube
from pytube import Playlist
import os

'''Python 3 Script'''


def youtubedownload():
    url = input('Please enter the URL:  ')
    print('Downloading... Please Wait... ')
    ytd = YouTube(url)
    stream = ytd.streams.filter(progressive=True, file_extension='mp4').order_by(
        'resolution').desc().first()
    stream.download(timeout=100000)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ytd)


youtubedownload()
input('Enter To Continue... ')

while True:
    youtubedownload()
