from pytube import YouTube
from pytube import Playlist
import os

'''Python 3 Script'''

def youtubedownload():
	url = input('Please enter the URL:  ')
	print('Downloading... Please Wait... ')
	ytd = YouTube(url).streams.first().download()
	print(ytd)

youtubedownload()
input('Enter To Continue... ')
os.system('cls' if os.name == 'nt' else 'clear')
while True:
	youtubedownload()
