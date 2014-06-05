import sys
import soundcloud
import pyen

#Configuration
pyen_key = "8GDKECFTIJHEADTWC" #echonest
client_id = "53188e4558d06691aac3cf57ef3a7cd7" #soundcloud
# Setting things up
en = pyen.Pyen(pyen_key)
client = soundcloud.Client(client_id=client_id)


# Dicts are resource heavy. Avoid them wherever possible.

def song_info(root_artist, root_track):
	""" Takes in track/artist as arguments and returns a list with related information"""
	templist=[]
	track_response = en.get('song/search', artist=root_artist, title=root_track, bucket=['audio_summary'], results=1)
	for track in track_response['songs']:
		root_duration = track["audio_summary"]['duration']

	templist.append(root_artist)
	templist.append(root_track)
	templist.append(sc_streamurl(root_track, root_artist, root_duration))

	return templist


def aukfetch(size, root_track, root_artist = None):
	"""Takes in track/(artist) and size as arguments and returns size number of related track info as a dict"""

	## Including size as an argument helps in realizing dynamic playlists.
	relatedtracks_response = en.get('playlist/static', artist=root_artist, type='artist-radio', results=size)
	return relatedtracks_response


def sc_streamurl(root_track, root_artist, root_duration):
	"""Returns a soundcloud stream url for a given track input"""

	tracks = client.get('/tracks', q=root_artist+' '+root_track, duration={'from': root_duration-2,'to': root_duration+2}, results=3)

	try:
		su =tracks[0].stream_url
		surl = client.get(su, allow_redirects=False)
		return surl.location
	except:
		try:
			su =tracks[1].stream_url
			surl = client.get(su, allow_redirects=False)
			return surl.location
		except:
			#print "[DEBUG]: Stream URL not found"
			pass