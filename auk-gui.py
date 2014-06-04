import sys
from PyQt4 import QtGui, QtCore

import auk
import gobject
import pygst
pygst.require("0.10")
import gst


class aukWindow(QtGui.QWidget):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		self.initiate_audio_sink()
		self.setWindowTitle("Auk Recommendation Service")
		self.layout = QtGui.QGridLayout(self)

		self.trackedit = QtGui.QLineEdit(self)
		self.trackedit.setPlaceholderText("Enter track name")

		self.artistedit = QtGui.QLineEdit(self)
		self.artistedit.setPlaceholderText("Enter artist name")

		self.button = QtGui.QPushButton("Search",self)
		self.button.setEnabled(False)

		self.table = QtGui.QTableWidget(self)
		self.table.setColumnCount(4)
		self.table.setWordWrap(True)
		self.table.setSortingEnabled(False)
		self.table.setHorizontalHeaderLabels(["S.no","Play","Track","Artist"])
		self.table.verticalHeader().setVisible(False)
		self.table.setAlternatingRowColors(True)
		self.table.setRowCount(10)
		self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.table.setMinimumWidth(500)
		self.table.setMinimumHeight(300)
		self.table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		self.table.horizontalHeader().setStretchLastSection(True)
		self.table.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

		self.table.setColumnWidth(0,35)
		self.table.setColumnWidth(1,50)
		self.table.setColumnWidth(2,300)


		self.statusinfo = QtGui.QLabel(self)
		self.statusinfo.setText("Welcome.")


		self.layout.addWidget(self.trackedit,1,0)
		self.layout.addWidget(self.artistedit,1,1)
		self.layout.addWidget(self.button,1,2)
		self.layout.addWidget(self.table,2,0,1,3)
		self.layout.addWidget(self.statusinfo,3,0)

		self.trackedit.textChanged.connect(self.enablebutton)
		self.button.clicked.connect(self.fetch_and_update)
		self.table.itemPressed.connect(self.play_track)


		#self.cb = QtGui.QApplication.clipboard()

		self.songsplayed = 0
		self.show()

	def on_message(self,bus,message):
		print "I am here"
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
			self.table.item(self.now_playing,1).setIcon(QtGui.QIcon.fromTheme('media-playback-start'))
		elif t == gst.MESSAGE_ERROR:
			err, debug = message.parse_error()
			self.player.set_state(gst.STATE_NULL)
			self.table.item(self.now_playing,1).setIcon(QtGui.QIcon.fromTheme('media-playback-start'))
			print "Error is %s" % err, debug


	def initiate_audio_sink(self):
		self.player = gst.element_factory_make("playbin", "player")
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.enable_sync_message_emission()
		bus.connect("message",self.on_message)
		print "Created BUS"

	#def toclipboard(self):
	#	self.cb.setText(self.related_songs_dict[self.now_playing,2])

	def play_track(self,item):

		if item.column() != 1:
			return False


		irow=item.row()
		# When sorted the rows might get mangled.
		irowactual= int(self.table.item(irow,0).text())

		#print "DEBUG", irowactual

		starticon = QtGui.QIcon.fromTheme('media-playback-start')
		pauseicon = QtGui.QIcon.fromTheme('media-playback-pause')

		song_uri = self.related_songs_dict[irowactual][2]

		
		if "PLAYING" in str(self.player.get_state()[1]):  ##playing
			self.songplayed = 1

			if song_uri == self.player.get_property('uri'):
				self.player.set_state(gst.STATE_PAUSED)
				item.setIcon(starticon)
				self.now_playing = irowactual
			else:
				self.table.item(self.now_playing,1).setIcon(starticon)
				self.player.set_state(gst.STATE_NULL)
				self.player.set_property('uri',song_uri)
				self.player.set_state(gst.STATE_PLAYING)
				item.setIcon(pauseicon)
				self.now_playing = irowactual
		else:
			if song_uri == self.player.get_property('uri'):
				self.player.set_state(gst.STATE_PLAYING)
				item.setIcon(pauseicon)
				self.now_playing = irowactual
			else:
				if self.songsplayed:
					self.table.item(self.now_playing,1).setIcon(starticon)
				self.player.set_state(gst.STATE_NULL)
				self.player.set_property('uri',song_uri)
				self.player.set_state(gst.STATE_PLAYING)
				self.songplayed = 1
				item.setIcon(pauseicon)
				self.now_playing = irowactual

	def enablebutton(self):
		if self.trackedit.text() == "":
			self.button.setEnabled(False)
		else:
			self.button.setEnabled(True)

	def fetch_and_update(self):
		self.statusinfo.setText("Fetching results. Please stand by.")
		QtGui.QApplication.processEvents()
		self.artistinfo = self.artistedit.text()
		self.trackinfo = self.trackedit.text()

		self.related_songs_dict = auk.aukfetch(str(self.trackinfo),str(self.artistinfo))

		for key,value in self.related_songs_dict.iteritems():

			sitem = QtGui.QTableWidgetItem(str(key))
			self.table.setItem(key,0,sitem)

			
			pitem = QtGui.QTableWidgetItem()
			

			if not value[2]:
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

			artistitem=QtGui.QTableWidgetItem(value[0])
			self.table.setItem(key,3,artistitem)

			trackitem=QtGui.QTableWidgetItem(value[1])
			self.table.setItem(key,2,trackitem)

		resultText = "Showing songs similar to "+"<b>"+self.trackinfo+"</b>"+"-"+"<b>"+self.artistinfo+"</b>"
		self.statusinfo.setText(resultText)

		self.artistedit.setText("")
		self.trackedit.setText("")

def main():
	gobject.threads_init()
	app = QtGui.QApplication(sys.argv)
	appins = aukWindow()
	sys.exit(app.exec_())

if __name__ == "__main__":
	main()