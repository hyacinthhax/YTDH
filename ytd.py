from pytube import YouTube
from pytube import Playlist
import os

'''Python 3 Script'''

def youtubedownload():
	url = input('Please enter the URL:  ')
	ytd = YouTube(url).streams.first().download()
	print('Downloading... ')
	print(ytd)

youtubedownload()
input('Enter To Continue... ')
os.system('cls' if os.name == 'nt' else 'clear')
youtubedownload()