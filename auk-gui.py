from __future__ import division
import sys
from PyQt4 import QtGui, QtCore ## Maybe you can trim down the depends by importing widgets directly
import auk
# Would have been brilliant if Phonon had behaved properly. gst is kickass.
import gobject
import pygst
pygst.require("0.10")
import gst
import webbrowser
import json
import tempfile
import os
import urllib2


from urllib import quote

##Subclassing Qtablewidget to have a right click menu 
class mTablewidet(QtGui.QTableWidget):
	tweetsignal = QtCore.pyqtSignal()

	def __init__(self):
		QtGui.QTableWidget.__init__(self)

	def contextMenuEvent(self,event):
		self.tweetsignal.emit()
		return QtGui.QTableWidget.contextMenuEvent(self,event)


## Subclassing qslider to dynamically display tooltip
class mSlider(QtGui.QSlider):
	show_tooltip = QtCore.pyqtSignal(object)
	slider_released = QtCore.pyqtSignal(object)

	def __init__(self):
		QtGui.QSlider.__init__(self)

	def mouseMoveEvent(self, event):
		self.show_tooltip.emit(event) # sending event to help figure the x cordinate of the slider
		return QtGui.QSlider.mouseMoveEvent(self, event)

	def mouseReleaseEvent(self,event): 
		self.slider_released.emit(event)
		return QtGui.QSlider.mouseReleaseEvent(self,event)

	# To ensure a chop free slider step ( Defeating pageStep and singleStep )
	def mousePressEvent(self,event):
		self.setValue(self.minimum() + ((self.maximum()-self.minimum()) * event.x()) / self.width() )
		return QtGui.QSlider.mousePressEvent(self,event)

# Thread which is responsible for fetching the content.
class fetchInfoThread(QtCore.QThread):
	fetch_complete = QtCore.pyqtSignal(object)

	def __init__(self,root_artist,root_track,key,url, duration):
		QtCore.QThread.__init__(self)
		self.root_artist = root_artist
		self.root_track = root_track
		self.key = key
		self.url= url
		self.duration = int(duration)/1000

	def run(self):
		songinfo = auk.song_info(self.root_artist, self.root_track, self.duration)
		songinfo.append(self.key)
		songinfo.append(self.url)
		songinfo.append(self.duration)

		self.fetch_complete.emit(songinfo)


class albumartThread(QtCore.QThread):
	afetch_complete = QtCore.pyqtSignal(object)
	def __init__(self,url):
		QtCore.QThread.__init__(self)
		self.url = url

	def run(self):
		data = urllib2.urlopen(self.url)
		self.afetch_complete.emit(data)


class aukWindow(QtGui.QWidget):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		self.initiate_audio_sink()
		self.setWindowTitle("Auk Recommendation Service")
		self.layout = QtGui.QGridLayout(self)

		## Track input
		self.trackedit = QtGui.QLineEdit(self)
		self.trackedit.setPlaceholderText("Enter track name")

		##Artist input
		self.artistedit = QtGui.QLineEdit(self)
		self.artistedit.setPlaceholderText("Enter artist name")

		## Search button
		self.button = QtGui.QPushButton("Search",self)
		self.button.setEnabled(False)

		## Tablewidget
		#self.table = QtGui.QTableWidget(self)
		self.table = mTablewidet()
		self.table.setColumnCount(4)
		self.table.setWordWrap(True)
		self.table.setSortingEnabled(False)
		self.table.setHorizontalHeaderLabels(["S.no","Play","Track","Artist"])
		self.table.verticalHeader().setVisible(False)
		self.table.setAlternatingRowColors(True)
		self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.table.setMinimumWidth(570)
		self.table.setMinimumHeight(300)
		self.table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
		self.table.setColumnWidth(0,35)
		self.table.setColumnWidth(1,50)
		self.table.setColumnWidth(2,300)
		self.table.hideColumn(0)

		## Status bar
		self.statusinfo = QtGui.QLabel(self)
		self.statusinfo.setText("<b>Welcome.</b>")

		## Slider
		self.slider = mSlider()
		self.slider.setOrientation(QtCore.Qt.Horizontal)
		#self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
		self.slider.setMouseTracking(True) ## Enables dynamic tooltips as implemented in the code.
		self.slider.setRange(0,100)
		#hell yeah
		self.slider.show_tooltip.connect(self.display_slider_tooltip)
		self.slider.slider_released.connect(self.slider_seek_released)
		#stylesheets
		self.slider.setStyleSheet("""
									QSlider::groove:horizontal {
     									background: white;
     									height : 2px;
     									border: 1px solid #bbb;
     									border-radius: 4px;
 									}

									 QSlider::handle:horizontal {
									 	background: silver;
									    border: 1px solid #777;
										width: 14px;
										margin-top: -7px;
										margin-bottom: -7px;
										border-radius: 7px;
									 }

									 QSlider::add-page:horizontal {
									     background: dark gray;
									 }

									 QSlider::sub-page:horizontal {
									     background: light gray;
									 }
									 """)

		## Now playing info button
		self.frame = QtGui.QFrame(self)
		self.frame.setFrameShadow(QtGui.QFrame.StyledPanel| QtGui.QFrame.Sunken) 
		self.framelayout = QtGui.QHBoxLayout(self.frame)

		self.albumartlabel = QtGui.QLabel(self.frame)
		self.nowplayinglabel = QtGui.QLabel(self.frame)

		self.framelayout.addWidget(self.albumartlabel,0)
		self.framelayout.addWidget(self.nowplayinglabel,1)

		## Adding widgets to the layout.
		self.layout.addWidget(self.trackedit,1,0)
		self.layout.addWidget(self.artistedit,1,1,1,2)
		self.layout.addWidget(self.button,1,3)
		self.layout.addWidget(self.table,2,0,1,4)
		self.layout.addWidget(self.frame,3,0)
		self.layout.addWidget(self.slider,3,3)
		self.layout.addWidget(self.statusinfo,4,0)

		## Intialization functions
		self.create_systray()
		self.create_appmenu()

		## The signals.
		self.artistedit.textChanged.connect(self.enablebutton)
		self.button.clicked.connect(self.fetch_and_update)
		self.table.itemPressed.connect(self.play_track)
		self.artistedit.textChanged.connect(self.enablebutton)
		self.slider.sliderMoved.connect(self.disable_slider_update)
		self.slider.sliderReleased.connect(self.enable_slider_update)
		self.table.tweetsignal.connect(self.show_rightclickmenu)
		

		## Timer updates self.slider every 1 second.
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update_slider)
		self.timer.start(1000)

		#self.cb = QtGui.QApplication.clipboard()

		# This indicates whether a track is being played at a given moment.
		self.is_playing = False
		# This indicates whether a song has been played in the session's lifetime.
		self.songsplayed = 0
		# Helps avoid a refetch loop.
		self.refresh_done = 0
		# Counts the resources fetched
		self.fcount = 0
		## Helps avoid conflict during seeking
		self.setting_value = 0

		self.show()

	def set_playinginfo(self):

		self.albumartlabel.setText("") # replaces the ablum art, Set it only when fetch is complete
		self.nowplayinglabel.setText("<b>  %s</b><br><b>  %s</b>" % (self.related_songs_dict[self.now_playing][1],self.related_songs_dict[self.now_playing][0])) 

		athreadworker = albumartThread(self.related_songs_dict[self.now_playing][4])
		athreadworker.afetch_complete.connect(self.set_album_art)
		self.threads.append(athreadworker)
		athreadworker.start()

	def set_album_art(self,data):
		tfile = tempfile.NamedTemporaryFile(delete=False)
		tfile.write(data.read())
		tfile.close()

		lfile = QtCore.QFile(tfile.name)
		lfile.open(QtCore.QIODevice.ReadOnly)
		ldata = lfile.map(0,lfile.size())
		lpix = QtGui.QPixmap()
		lpix.loadFromData(ldata)

		os.unlink(tfile.name)
		self.albumartlabel.setPixmap(lpix)


	def create_appmenu(self):
		self.appmenu = QtGui.QMenu(self)

		self.tweetAction = QtGui.QAction("Tweet now playing",self,triggered=self.tweet_nowplaying)
		self.tweetAction.setDisabled(True)

		self.appmenu.addAction(self.tweetAction)
		self.appmenu.addAction(self.aboutAction)

	def show_rightclickmenu(self):
		self.appmenu.popup(QtGui.QCursor.pos())

	def tweet_nowplaying(self):
		content="#nowplaying %s-%s on #Auk" % (self.related_songs_dict[self.now_playing][1],self.related_songs_dict[self.now_playing][0])
		URL = "https://twitter.com/intent/tweet?text=" + quote(content)
		webbrowser.open(URL)

	def create_systray(self):
		self.minimizeAction = QtGui.QAction("Minimize",self,triggered=self.hide)
		self.restoreAction = QtGui.QAction("Restore",self,triggered=self.showNormal)
		self.aboutAction = QtGui.QAction("About",self,triggered=self.show_about)
		self.quitAction = QtGui.QAction("Quit",self,triggered=QtGui.qApp.quit)

		self.traymenu = QtGui.QMenu(self)
		self.traymenu.addAction(self.minimizeAction)
		self.traymenu.addAction(self.restoreAction)
		self.traymenu.addAction(self.aboutAction)
		self.traymenu.addSeparator()
		self.traymenu.addAction(self.quitAction)

		self.trayIcon = QtGui.QSystemTrayIcon(self)
		self.trayIcon.setContextMenu(self.traymenu)
		self.trayIcon.setIcon(QtGui.QIcon.fromTheme('media-playback-start'))
		self.trayIcon.show()
		
	def show_about(self):
		self.showNormal()
		self.aboutmbox = QtGui.QMessageBox(self)
		self.aboutmbox.setText("<b>Auk Version 0.1</b><br><br>Homepage: https://github.com/slotlocker2/Auk</br></br><br>Powered by Soundcloud and EchoNest.</br>")
		self.aboutmbox.exec_()

	def disable_slider_update(self):
		self.setting_value = 1

	def enable_slider_update(self):
		self.setting_value = 0

	def refetch_track(self):
		self.statusinfo.setText("Trying to refetch the track. Stand by")
		QtGui.QApplication.processEvents()

		tempinfo = self.related_songs_dict[self.now_playing]

		temptrack = tempinfo[1]
		tempartist = tempinfo[0]
		tempduration = tempinfo[5]

		tempurl = auk.song_info(tempartist,temptrack,tempduration)[2]

		self.related_songs_dict[self.now_playing][2] = tempurl

		self.statusinfo.setText("<b>%s-%s</b> refetched." % (temptrack, tempartist,))
		QtGui.QApplication.processEvents()

		self.refresh_done = 1
		self.play_track(self.table.item(self.now_playing,1))

	def convert_ns(self,value):
		tsecs = value/1e9
		## add hours if needed
		minutes = str(tsecs/60).split(".")[0]
		seconds = str(tsecs % 60).split(".")[0]

		return minutes+":"+seconds

	def display_slider_tooltip(self,event):
		if not "NULL" in str(self.player.get_state()[1]):
			#QtGui.QToolTip.showText(event.globalPos(), str(-1), self) ## Constantly change the value so that the tooltip follows the pointer
			## as read in the qt docs
			percentage_pos = round(((self.slider.minimum() + (self.slider.maximum() - self.slider.minimum()))*event.x())/self.slider.width(),2)
			play_pos = (percentage_pos*self.play_duration())/100
			tool_text = self.convert_ns(play_pos)+"/"+self.convert_ns(self.play_duration())+"\n"+"  "+str(percentage_pos)+"%"

			QtGui.QToolTip.showText(event.globalPos(), tool_text, self)

	def slider_seek_released(self,event):
		self.setting_value = 1
		if not "NULL" in str(self.player.get_state()[1]):
			percentage_pos = round(((self.slider.minimum() + (self.slider.maximum() - self.slider.minimum()))*event.x())/self.slider.width(),2)
			play_pos = (percentage_pos*self.play_duration())/100
			self.player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, play_pos)
		self.setting_value = 0

	def play_duration(self):
		"""Returns the duration of the song in nano seconds. """
		duration_nanosecs, duration_format = self.player.query_duration(gst.FORMAT_TIME)
		return duration_nanosecs

	def play_position(self):
		"""Returns the position of the song in nanoseconds"""
		position_nanosecs, position_format = self.player.query_position(gst.FORMAT_TIME)
		return position_nanosecs

	def fetch_position(self):
		"""Returns the percentage of song that has been played"""
		try:
			return (self.play_position()/self.play_duration())*100
		except gst.QueryError:
			# pipeline does not know position yet
			pass

	def update_slider(self):
		"""Updates the position of the slider based on the position of the current track being played"""

		if not self.is_playing:
			return False
		else:
			if not self.setting_value:
				try:
					self.slider.setValue(self.fetch_position())
				except:
					return False

	def on_message(self,bus,message):
		""" End of track and error handling of gst"""
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
			self.slider.setValue(0)
			self.is_playing = False
			self.table.item(self.now_playing,1).setIcon(QtGui.QIcon.fromTheme('media-playback-start'))
			## code which enables continuous playback.
			self.play_next()
		elif t == gst.MESSAGE_ERROR:
			#err, debug = message.parse_error()  ## Uncomment for debug.
			self.player.set_state(gst.STATE_NULL)
			self.slider.setValue(0)
			self.is_playing = False
			self.table.item(self.now_playing,1).setIcon(QtGui.QIcon.fromTheme('media-playback-start'))
			#[DEBUG]: print "Error is %s" % err, debug
			if self.refresh_done:
				self.statusinfo.setText("Something wicked happened.")
				QtGui.QApplication.processEvents()
			else:
				self.refetch_track()
			
	def play_next(self):

		## Can't include all of it inside the while loop since the play order is random.
		counter = self.now_playing + 1

		try:
			while not self.related_songs_dict[counter][2]:
				counter = counter + 1
		except:
			#print "[DEBUG] Finished reading list."
			pass

		if counter <= self.table.rowCount()-1: # checks if item exists (avoided harcoding it to 10)
			self.play_track(self.table.item(counter,1))
		else:
			pass

	def initiate_audio_sink(self):
		""" Sets up the playbin and the bus for audio playback."""
		self.player = gst.element_factory_make("playbin", "player")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect("message",self.on_message)
		print "[DEBUG] Created audio kit for playback."


	#def toclipboard(self):
	#	self.cb.setText(self.related_songs_dict[self.now_playing,2])

	def play_track(self,item):
		"""Plays, pauses and stops tracks in response to the tablwwidgetitem clicks """
		if item.column() != 1:
			return False


		irow=item.row()
		# When sorted the rows might get mangled.
		irowactual= int(self.table.item(irow,0).text())

		#print "[DEBUG]", irowactual

		starticon = QtGui.QIcon.fromTheme('media-playback-start')
		pauseicon = QtGui.QIcon.fromTheme('media-playback-pause')

		song_uri = self.related_songs_dict[irowactual][2]

		
		if "PLAYING" in str(self.player.get_state()[1]):  ##playing
			self.songplayed = 1

			if song_uri == self.player.get_property('uri'):
				self.player.set_state(gst.STATE_PAUSED)
				self.is_playing = False
				item.setIcon(starticon)
				self.now_playing = irowactual
				self.tweetAction.setDisabled(True)
			else:
				## Here is where the song chnages while playing.
				self.table.item(self.now_playing,1).setIcon(starticon)
				self.player.set_state(gst.STATE_NULL)
				self.player.set_property('uri',song_uri)
				## Having this before the track starts playing helps in re - fetching the track should the link expire.
				self.now_playing = irowactual
				self.player.set_state(gst.STATE_PLAYING)
				self.is_playing = True
				item.setIcon(pauseicon)
				QtGui.QApplication.processEvents()
				self.trayIcon.showMessage("Now Playing", "%s-%s" % (self.related_songs_dict[self.now_playing][1],self.related_songs_dict[self.now_playing][0]),QtGui.QSystemTrayIcon.Information,3000)
				self.set_playinginfo()
				self.tweetAction.setDisabled(False)
				
		else:
			## Here is where the song resumes playing after kicked back to life from a paused state.
			if song_uri == self.player.get_property('uri'):
				self.player.set_state(gst.STATE_PLAYING)
				self.is_playing = True
				item.setIcon(pauseicon)
				self.now_playing = irowactual
				self.tweetAction.setDisabled(False)
			else:
				## Here is where a song kicks off when there is no song playing.
				if self.songsplayed:
					self.table.item(self.now_playing,1).setIcon(starticon)
				self.player.set_state(gst.STATE_NULL)
				self.player.set_property('uri',song_uri)
				# Refer to the above function for the reason this comes before gst is set to play.
				self.now_playing = irowactual
				self.player.set_state(gst.STATE_PLAYING)
				self.is_playing = True
				self.songplayed = 1
				self.refresh_done = 0
				item.setIcon(pauseicon)
				QtGui.QApplication.processEvents()
				self.trayIcon.showMessage("Now Playing", "%s-%s" % (self.related_songs_dict[self.now_playing][1],self.related_songs_dict[self.now_playing][0]),QtGui.QSystemTrayIcon.Information,3000)
				self.set_playinginfo()
				self.tweetAction.setDisabled(False)
				
	def enablebutton(self):
		"""Enables search button only when the track edit field is not empty"""
		if self.artistedit.text() == "" or self.trackedit == "":
			self.button.setEnabled(False)
		else:
			self.button.setEnabled(True)

	def on_fetch_data(self,songinfo):
		key = songinfo[3]

		sitem = QtGui.QTableWidgetItem(str(key))
		self.table.setItem(key,0,sitem)

		pitem = QtGui.QTableWidgetItem()
		if not songinfo[2]:
			pitem.setFlags( QtCore.Qt.NoItemFlags )
			icon = QtGui.QIcon.fromTheme('dialog-warning')
			pitem.setIcon(icon)
			self.table.setItem(key,1,pitem)
			pitem.setToolTip("URL not found.")
		else:
			icon = QtGui.QIcon.fromTheme('media-playback-start')
			pitem.setFlags( QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled )
			pitem.setIcon(icon)
			self.table.setItem(key,1,pitem)

		artistitem=QtGui.QTableWidgetItem(songinfo[0])
		self.table.setItem(key,3,artistitem)

		trackitem=QtGui.QTableWidgetItem(songinfo[1])
		self.table.setItem(key,2,trackitem)

		## The master dictionary that holds the info about ALL the songs.
		self.related_songs_dict[key] = songinfo

		self.fcount = self.fcount + 1
		
		stext = "Fetching result %d / %d. Please stand by." % (self.fcount,self.COUNT,)
		self.statusinfo.setText(stext)
		QtGui.QApplication.processEvents()

		if self.fcount == 10:
			resultText = "Showing songs similar to "+"<b>"+self.trackinfo+"</b>"+"-"+"<b>"+self.artistinfo+"</b>"
			self.statusinfo.setText(resultText)
			self.artistedit.setText("")
			self.trackedit.setText("")
			self.fcount = 0

	def fetch_and_update(self):
		"""Queries the auk backend for the track listing. Fetches a dict"""
		self.COUNT = 10
		# Clear all the rows and reallocate.
		self.table.setRowCount(0)
		self.table.setRowCount(self.COUNT)

		self.artistinfo = self.artistedit.text()
		self.trackinfo = self.trackedit.text()
		self.related_songs_dict = {}

		try:
			rresponse = auk.aukfetch(self.COUNT, str(self.trackinfo),str(self.artistinfo))
			related_response = json.load(rresponse)

			stext = "Fetching result %d / %d. Please stand by." % (self.fcount+1,self.COUNT)
			self.statusinfo.setText(stext)
			QtGui.QApplication.processEvents()

			self.threads = []

			for key,new_track in enumerate(related_response['similartracks']['track']):
				fetcher = fetchInfoThread(new_track['artist']['name'], new_track['name'],key,new_track['image'][1]['#text'],new_track['duration'])
				fetcher.fetch_complete.connect(self.on_fetch_data)
				self.threads.append(fetcher)
				fetcher.start()
		except:
			self.statusinfo.setText("<b>Could not find similar tracks.</b>")
			self.artistedit.setText("")
			self.trackedit.setText("")

		

def main():
	gobject.threads_init()
	app = QtGui.QApplication(sys.argv)
	appins = aukWindow()
	sys.exit(app.exec_())


if __name__ == "__main__":
	main()


	## TO DO:
	## 3. integrate last.fm
	## Move away from echonest to last fm
	## 2. Internet not available notification
