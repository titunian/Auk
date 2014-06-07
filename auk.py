import sys
import soundcloud
import urllib2

#Configuration
client_id = "53188e4558d06691aac3cf57ef3a7cd7" #soundcloud
lastfm_key = "f53c270502a8d4135bf6964d7719e50e"

# Setting things up
client = soundcloud.Client(client_id=client_id)


# Dicts are resource heavy. Avoid them wherever possible.

def song_info(root_artist, root_track, root_duration):
	""" Takes in track/artist as arguments and returns a list with related information"""
	templist=[]
	templist.append(root_artist)
	templist.append(root_track)
	templist.append(sc_streamurl(root_track, root_artist, root_duration))

	return templist


def aukfetch(size, root_track, root_artist):
	"""Takes in both the track and the artist and returns size number of related track info as a dict"""
	url = "http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist=%s&track=%s&api_key=%s&format=json&limit=%d&autocorrect=1" % (urllib2.quote(root_artist),urllib2.quote(root_track),lastfm_key,size)
	relatedtracks_response = urllib2.urlopen(url)
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
