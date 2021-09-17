from pytube import YouTube
from pytube import Playlist
import os

'''Python 3 Script'''

src = os.getcwd()

def youtubedownload():
	url = input('Please enter the URL:  ')
	print('Downloading... Please Wait... ')
	ytd = YouTube(url)
	stream = ytd.streams.get_by_itag(22)
	stream.download()
	os.system('cls' if os.name == 'nt' else 'clear')
	print("Downloaded " + url)
	for files in os.listdir(src):
		# print(files[-4:])
		if files[-4:] == ".mp4":
			print("Downloads Complete: {0}".format(files))

youtubedownload()
input('Enter To Continue... ')

while True:
	youtubedownload()
