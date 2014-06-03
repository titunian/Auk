import sys, soundcloud, pyen

#Configuration
pyen_key = "8GDKECFTIJHEADTWC" #echonest
client_id = "53188e4558d06691aac3cf57ef3a7cd7" #soundcloud
en = pyen.Pyen(pyen_key)
client = soundcloud.Client(client_id=client_id)
def auk(root_track, root_artist = None):

	response = en.get('song/search', artist=root_artist, title=root_track, bucket=['audio_summary'], results=1)
	
	for song in response['songs']:
		root_duration = song["audio_summary"]['duration']
	#print root_duration
	root_artist = song["artist_name"]
	root_track = song["title"]
	#handle exceptions for license
	print "root %-32.32s %s" % (root_artist, root_track)
	print sc_streamurl(root_track, root_artist, root_duration)
	response = en.get('playlist/static', artist=root_artist, type='artist-radio', results=50)


	for i, new_song in enumerate(response['songs']):
		response2 = en.get('song/search', artist=new_song['artist_name'], title=new_song['title'], bucket=['audio_summary'], results=1)
		for song in response2['songs']:
			new__duration = song["audio_summary"]['duration']
		print "%d %-32.32s %s" % (i, new_song['artist_name'], new_song['title'])
		print sc_streamurl(new_song['title'], new_song['artist_name'], new__duration)


def sc_streamurl(root_track, root_artist, root_duration):
	"""
	Gives back the soundcloud stream url for a given track input
	"""
	tracks = client.get('/tracks', q=root_artist+' '+root_track, duration={'from': root_duration-2,'to': root_duration+2}, results=3)
	try:
		#print tracks[0].title
		su =tracks[0].stream_url
		stream_url = client.get(su, allow_redirects=False)

	# print the tracks stream URLnj
		return stream_url.location
	except:
		#print tracks[1].title
		try:
			su =tracks[1].stream_url
			stream_url = client.get(su, allow_redirects=False)
			return stream_url.location
		except:
			pass

print "Welcome to auk-0.1","\n"
root_track= raw_input("Enter track name:  ")
root_artist = raw_input("Enter artist name: ")

auk(root_track, root_artist)