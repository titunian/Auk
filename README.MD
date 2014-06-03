-------------------------------------------------------------------------------------------------------
Auk Music 0.1
==============


Auk is a soundcloud-echonest based radio which returns http streams of similar tracks(radio) to the root_track


1. How to setup:
-----------------

Make sure you have all the packages mentioned in requirements.txt

Visit [developers.soundcloud.com](developers.soundcloud.com) and register your app. Get your `client_id` and replace my `client_id`. This is important since my client_id allows only limited connections and the script might not run properly.
Similarly, register your app at Echonest and replace the `pyen_key`

2. Running the program:
-----------------------

```
 python auk.py
 ```
  Enter the CORRECT track and artist names to get a list of http streams of the tracks similar to your input track from soundcloud.
 
3. Output
---------

```
track_id  artist_name               track_name
```
  
4.Usage:
--------
 You can modify the script to create a webplayer which plays the sounds or you can copy paste the http stream url in your browser and listen to them.
 OR you can always note the track names and play using services like Spotify.
  

5. Dependencies
-----------

Dependencies can be installed by running the command - `pip install -r requirements.txt`.
add 'sudo' if required.

1. Soundcloud 0.4.1
2. pyen 2.3