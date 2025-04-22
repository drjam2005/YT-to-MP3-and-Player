import os
import sys
import shutil
import yt_dlp
from math import ceil
from mutagen.mp3 import MP3
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtWidgets import QSpacerItem, QApplication, QWidget, QGridLayout, QDialog, QTextEdit, QLineEdit,  QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget, QSlider

ydl_opts = {
    'format': 'mp3/bestaudio/best',
    'postprocessors': [{ 
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl' : "%(title)s.%(ext)s",
}

class AddSongsWidget(QDialog):
    def __init__(self, args):
        super().__init__()
        self.resize(350, 300)
        self.songs = ""
        
        self.HbottomLayout = QHBoxLayout()
        self.Vlayout = QVBoxLayout()
        
        self.label = QLabel("Add Youtube Link/s: ")
        self.input = QTextEdit()
        self.confirmButton = QPushButton("Confirm")
        self.cancelButton = QPushButton("Cancel")

        self.HbottomLayout.addWidget(self.confirmButton)
        self.HbottomLayout.addWidget(self.cancelButton)
        
        self.confirmButton.clicked.connect(self.confirm)
        self.cancelButton.clicked.connect(self.cancel)
        
        self.Vlayout.addWidget(self.label)
        self.Vlayout.addWidget(self.input)
        self.Vlayout.addLayout(self.HbottomLayout)
        self.setLayout(self.Vlayout)

    def confirm(self):
        self.songs = self.input.toPlainText()
        self.close()
    
    
    def cancel(self):
        self.close()

class DownloadSignals(QObject):
    starting = pyqtSignal()
    progress = pyqtSignal(int)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

class DownloadSongs(QRunnable):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.signals = DownloadSignals()
    
    @pyqtSlot()
    def run(self):
        links = self.args[0]
        downloadPath = self.args[1]
        
        ydl_copyOpts = ydl_opts.copy()
        ydl_copyOpts['outtmpl'] = downloadPath + "\\" + "%(title)s.%(ext)s"
        
        indx = 1
        self.signals.starting.emit()
        for link in links:
            with yt_dlp.YoutubeDL(ydl_copyOpts) as ydl:
                try:
                    ydl.download(link)
                except:
                    print("error! skipping!")
                    self.signals.error.emit(str(link))
                self.signals.progress.emit(indx)
                indx += 1
        self.signals.finished.emit(len(self.args[0]))
       
class CreatePlaylistWidget(QDialog):
    def __init__(self, args):
        super().__init__()
        self.resize(250, 100)
        self.playlistname = ""
        
        self.HtopLayout = QHBoxLayout()
        self.HbottomLayout = QHBoxLayout()
        self.Vlayout = QVBoxLayout()
        self.Vlayout.addLayout(self.HtopLayout)
        self.Vlayout.addLayout(self.HbottomLayout)
        
        self.label = QLabel("Playlist Name: ")
        self.lineEdit = QLineEdit()
        self.confirmButton = QPushButton("Confirm")
        self.cancelButton = QPushButton("Cancel")

        self.HtopLayout.addWidget(self.label)
        self.HtopLayout.addWidget(self.lineEdit)
        self.HbottomLayout.addWidget(self.confirmButton)
        self.HbottomLayout.addWidget(self.cancelButton)
        
        self.confirmButton.clicked.connect(self.confirm)
        self.cancelButton.clicked.connect(self.cancel)
        
        self.setLayout(self.Vlayout)
        
        
    def confirm(self):
        self.playlistname = self.lineEdit.text()
        self.close()


    def cancel(self):
        self.close()

class DeleteDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.resize(200,150)
        self.args = args
        self.kwargs = kwargs
        self.delete = None

        name = self.args[1]
        type = self.args[0]

        self.Layout = QVBoxLayout()
        self.HLayout = QHBoxLayout()
        self.label = QLabel(f"Are you sure you want to delete")
        self.label2 = QLabel(f"{type}: {name}?")
        self.confirmButton = QPushButton("Yes")
        self.cancelButton = QPushButton("No")

        self.label2.setFont(QFont('Trebuchet MS', 10))
        self.confirmButton.clicked.connect(self.push)
        self.cancelButton.clicked.connect(self.push)

        self.HLayout.addWidget(self.confirmButton)
        self.HLayout.addWidget(self.cancelButton)

        self.Layout.addWidget(self.label)
        self.Layout.addWidget(self.label2)
        self.Layout.addLayout(self.HLayout)
        
        self.setLayout(self.Layout)

    def push(self):
        if self.sender().text() == "Yes":
            self.delete = True
        self.close()

class MainWidget(QWidget):
    def __init__(self, args):
        super().__init__()
        self.resize(500,400)
        self.setStyleSheet("QWidget{ background-color: #111;} QComboBox{color: #FFF; background-color:#444} QLabel{color: #FFF;} QPushButton{color: #FFF} QListView{color: #FFF} QPushButton{background-color: #444}")
        self.setMaximumSize(500,400)
        self.setMinimumSize(500,400)
        self.setWindowTitle("shit")
        self.songPlayer = QMediaPlayer()
        self.songPlayer.setVolume(100)
        self.currentMSeconds = 0
        self.isPlaying = False
        self.isLoop = False
        self.loadedSong = None
        self.songLength = None
        self.songLengthParsed = ""
        self.chosenSong = ""
        self.chosenPlaylist = ""
        self.setLayouts()
   
        
    def setWidgets(self):
        self.playButtons = QHBoxLayout()
        
        # top left
        self.choosePlaylist = QComboBox()
        self.playlistView = QListWidget()
        # top right
        self.blank = QLabel("")
        self.createPlaylist = QPushButton("Create Playlist")
        self.addSong = QPushButton("Add Song/s")
        self.deletePlaylist = QPushButton("Delete Playlist")
        self.deleteSong = QPushButton("Delete Song")
        self.warningLabel = QLabel("")
        self.errorLabel = QLabel("")
        
        # bottom
        self.Playing = QLabel("Playing: (song)")
        self.volumeSlider = QSlider(orientation=Qt.Horizontal)
        self.musicSlider = QSlider(orientation=Qt.Horizontal)
        self.timePlaying = QLabel("X:XX / X:XX")
        self.prevSong = QPushButton("<")
        self.togglePlayback = QPushButton("|>")
        self.nextSong = QPushButton(">")
        self.loop = QPushButton("Loop [X]")
        self.volumeAmount = QLabel("Volume: 100")

        # setup
        self.topLeftVbox.addWidget(self.choosePlaylist, 10)
        self.topLeftVbox.addWidget(self.playlistView, 90)  
        self.topRightVbox.addWidget(self.blank) # shit
        self.topRightVbox.addWidget(self.createPlaylist)
        self.topRightVbox.addWidget(self.addSong)
        self.topRightVbox.addWidget(self.warningLabel)
        self.topRightVbox.addWidget(self.errorLabel)
        self.topRightVbox.addWidget(self.blank) # so shit
        self.topRightVbox.addWidget(self.blank) # so shit
        self.topRightVbox.addWidget(self.deletePlaylist)
        self.topRightVbox.addWidget(self.deleteSong)
        self.topRightVbox.addWidget(self.blank)
        self.topRightVbox.addWidget(self.blank)
        self.topRightVbox.addWidget(self.volumeAmount)
        self.topRightVbox.addWidget(self.volumeSlider)
        
        self.playButtons.addWidget(self.timePlaying)
        self.playButtons.addWidget(self.prevSong)
        self.playButtons.addWidget(self.togglePlayback)
        self.playButtons.addWidget(self.nextSong)
        self.playButtons.addWidget(self.loop)
        self.playButtons.addWidget(self.blank)

        self.lowVbox.addWidget(self.Playing)
        self.lowVbox.addWidget(self.musicSlider)
        self.lowVbox.addLayout(self.playButtons)
        
        self.update_playlists()
        self.setEvents()
     
        
    def setLayouts(self):
        self.masterVbox = QVBoxLayout()
        
        self.topHbox = QHBoxLayout()
        self.topRightVbox = QVBoxLayout()
        self.topLeftVbox = QVBoxLayout()
        
        self.topHbox.addLayout(self.topLeftVbox, 70)
        self.topHbox.addLayout(self.topRightVbox, 30)

        self.gridBox = QGridLayout()
        self.lowVbox = QVBoxLayout()
        
        self.masterVbox.addLayout(self.topHbox, 70)
        self.masterVbox.addLayout(self.lowVbox, 30)
        
        self.setWidgets()
        self.setLayout(self.masterVbox)    
    
    
    def setEvents(self):
        self.choosePlaylist.currentTextChanged.connect(lambda chosen: self.update_song_list(chosen))
        self.playlistView.currentTextChanged.connect(lambda s: self.handleChoose(s))

        self.createPlaylist.clicked.connect(self.create_playlist)
        self.addSong.clicked.connect(self.add_song)
        
        self.deletePlaylist.clicked.connect(lambda: self.delete_item("playlist"))
        self.deleteSong.clicked.connect(lambda: self.delete_item("song"))
        
        self.prevSong.clicked.connect(lambda: self.iterateSong(user=-1))
        self.togglePlayback.clicked.connect(self.toggle_play_song)
        self.nextSong.clicked.connect(lambda: self.iterateSong(user=1))
        self.loop.clicked.connect(self.toggleLoop)
        
        
        self.volumeSlider.setValue(100)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.sliderMoved.connect(lambda val: (self.songPlayer.setVolume(val), self.volumeAmount.setText(f"Volume: {val}")))
        self.songPlayer.positionChanged.connect(lambda val: self.updateSlider(val))
        self.songPlayer.mediaStatusChanged.connect(lambda status: self.iterateSong(status=status))

        
        self.musicSlider.sliderReleased.connect(self.seekSlider)
    
    def handleChoose(self, str):
        self.chosenSong = str

    def iterateSong(self, status=None, user=0):
        if status == 2:
            return
        if not bool(user) and self.isLoop and not self.isPlaying:
            self.updateSlider(0)
            self.songPlayer.play()
            return
        if not self.isPlaying:
            return
        playlistPath = os.path.join("playlists", self.choosePlaylist.currentText())
        songList = [song for song in os.listdir(playlistPath) if song.endswith(".mp3")]
        if self.chosenSong == "":
            self.chosenSong = songList[0]
        playlistSize = len(songList)
        currentIndex = songList.index(self.chosenSong)

        setRow = currentIndex
        if user:
            if playlistSize <= 1:
                return
            elif currentIndex+1 == playlistSize:
                if user == 1:
                    setRow = 0
                elif user == -1:
                    setRow = setRow-1
            elif currentIndex == 0:
                if user == 1:
                    setRow = setRow+1
                elif user == -1:
                    setRow = playlistSize-1
            else:
                setRow = setRow+user
            self.chosenSong = songList[setRow]
            

        songUrl = os.path.join(playlistPath, self.chosenSong)

        self.playlistView.setCurrentRow(setRow)
        self.songLength = MP3(songUrl).info.length
        self.musicSlider.setMaximum(int(self.songLength*1000))

        minutes = int(self.songLength / 60)
        seconds = int(self.songLength) - (minutes*60)

        self.songLengthParsed = f"{minutes}:{seconds:02d}"
        self.timePlaying.setText("0:00 / " + self.songLengthParsed)

        self.loadedSong = QUrl.fromLocalFile(songUrl)
        self.songPlayer.stop()
        self.songPlayer.setMedia(QMediaContent(self.loadedSong))
        self.songPlayer.play()
        

    def toggleLoop(self):
        self.isLoop = not self.isLoop
        if self.isLoop:
            self.loop.setText("Loop [✓]")
        else:
            self.loop.setText("Loop [X]")
    
    def toggle_play_song(self):
        self.warningLabel.setText("")
        try:
            self.chosenPlaylist = self.choosePlaylist.currentText()
            self.chosenSong = self.playlistView.currentItem().text()
            songUrl = os.path.join("playlists", self.chosenPlaylist, self.chosenSong)
        except:
            self.warningLabel.setText("Please choose a song!")
            return
        
        if not os.path.exists(songUrl):
            self.warningLabel(f"{songUrl} does not exist!")
            return
        
        if self.loadedSong is None or (self.loadedSong != QUrl.fromLocalFile(songUrl)):
            self.songLength = MP3(songUrl).info.length
            self.musicSlider.setMaximum(int(self.songLength*1000))

            minutes = int(self.songLength / 60)
            seconds = int(self.songLength) - (minutes*60)

            self.songLengthParsed = f"{minutes}:{seconds:02d}"
            self.timePlaying.setText("0:00 / " + self.songLengthParsed)

            self.musicSlider.setValue(0)
            self.loadedSong = QUrl.fromLocalFile(songUrl)
            self.songPlayer.setMedia(QMediaContent(self.loadedSong))

        if not self.isPlaying:
            self.songPlayer.play()
            self.Playing.setText(f"Playing: {self.chosenSong.removesuffix(".mp3")}")
            self.togglePlayback.setText("||")
        elif self.isPlaying:
            self.songPlayer.pause()
            self.Playing.setText(f"Paused: {self.chosenSong.removesuffix(".mp3")}")
            self.togglePlayback.setText("|>")
            
        self.isPlaying = not self.isPlaying
             
    def updateSlider(self, val=0):
        self.currentMSeconds = val
        self.musicSlider.setValue(self.currentMSeconds)

        minutes = int(int(self.currentMSeconds/1000) / 60)
        seconds = round((self.currentMSeconds/1000) - (minutes * 60))

        liveTime = f" {minutes}:{seconds:02d} / {self.songLengthParsed}"
        self.timePlaying.setText(liveTime)
        
    def seekSlider(self):
        seeked = self.musicSlider.value()
        self.songPlayer.pause()
        self.songPlayer.setPosition(seeked)
        if self.isPlaying:
            self.songPlayer.play()
             
    def create_playlist(self):
        self.CreatePlaylistWindow = CreatePlaylistWidget([])
        self.CreatePlaylistWindow.exec()
        playlist_name = self.CreatePlaylistWindow.playlistname
        if playlist_name != "":
            path_name = os.path.join("playlists", playlist_name)
            if os.path.exists(path_name):
                self.warningLabel.setText(f"{playlist_name} already exsits!")
                return
            os.mkdir(path_name)
            self.update_playlists()
            self.choosePlaylist.setCurrentText(playlist_name)
    
        
    def add_song(self):
        currentPlaylist = self.choosePlaylist.currentText()
        if currentPlaylist == "":
            self.warningLabel.setText("Please create a playlist!")
            return
        fullpath = os.path.join("playlists",currentPlaylist)
        self.AddSongWindow = AddSongsWidget(currentPlaylist)
        self.AddSongWindow.exec()
        songs = self.AddSongWindow.songs.split('\n')
        if songs == ['']:
            return
        self.threadpool = QThreadPool()
        worker = DownloadSongs(songs, fullpath)
        worker.signals.progress.connect(lambda val: self.updateWarning(val, songs, currentPlaylist))
        worker.signals.error.connect(lambda song: self.errorLabel.setText(f"Couldn't download\n\"{song}\""))
        worker.signals.finished.connect(self.finishWarning)
        worker.signals.starting.connect(lambda: self.warningLabel.setText("Starting download/s..."))
        
        self.finished = False
        self.threadpool.start(worker)
        
    def updateWarning(self, val, songs, currentPlaylist):
        self.warningLabel.setText(f"Downloaded {val}/{len(songs)} songs...")
        self.update_song_list(currentPlaylist)
    
    def finishWarning(self, val):
        self.warningLabel.setText(f"Finished Downloading {val} songs!")
        self.update_song_list(self.choosePlaylist.currentText())
    
    def update_playlists(self):
        if not os.path.exists("playlists"):
            os.mkdir("playlists")
            self.warningLabel.setText("Please create a playlist!")
            return
        playlists = [playlist for playlist in os.listdir("playlists") if os.path.isdir(os.path.join("playlists", playlist))]
        self.choosePlaylist.clear()
        self.choosePlaylist.addItems(playlists)
        if playlists != [] and playlists is not None:
            self.update_song_list(playlists[0])

    def update_song_list(self, playlist):
        songs = [song for song in os.listdir(os.path.join("playlists", playlist)) if song.endswith(".mp3")]
        self.playlistView.clear()
        self.playlistView.addItems(songs)
        if songs != []:
            self.playlistView.setCurrentRow(0)
        
    def delete_item(self, str):
        self.warningLabel.setText("")
        if str == "playlist":
            item = self.choosePlaylist.currentText()
        elif str == "song":
            try:
                playlist = self.choosePlaylist.currentText()
                item = os.path.join(playlist, self.playlistView.currentItem().text())
            except AttributeError:
                self.warningLabel.setText("Please choose a song!")
                return
        deleteWindow = DeleteDialog(str, item)
        deleteWindow.exec()
        fullpath = os.path.join("playlists", item)
        if deleteWindow.delete:
            if os.path.isdir(fullpath):
                shutil.rmtree(fullpath)
            else:
                os.remove(fullpath)
        else:
            return
        self.update_playlists()
        
        

def main():
    app = QApplication(sys.argv)
    main_window = MainWidget(sys.argv)
    main_window.show()
    app.exec_()


if __name__ == "__main__":
    main()