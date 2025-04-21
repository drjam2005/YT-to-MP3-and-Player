import os
import sys
import time
import yt_dlp
from mutagen.mp3 import MP3
from PyQt5.QtCore import Qt, QUrl, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QTextEdit, QLineEdit,  QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QListWidget, QSlider

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
        
        print(self.args[0], self.args[1])

class MainWidget(QWidget):
    def __init__(self, args):
        super().__init__()
        self.resize(500,400)
        self.setWindowTitle("shit")
        self.setLayouts()
        self.songPlayer = QMediaPlayer()
        self.loadedSong = None
        self.isPlaying = False
        self.songLength = None
   
        
    def setWidgets(self):
        self.playButtons = QHBoxLayout()
        
        # top left
        self.choosePlaylist = QComboBox()
        self.playlistView = QListWidget()
        # top right
        self.blank = QLabel()
        self.createPlaylist = QPushButton("Create Playlist")
        self.addSong = QPushButton("Add Song/s")
        self.deletePlaylist = QPushButton("Delete Playlist")
        self.deleteSong = QPushButton("Delete Song")
        self.warningLabel = QLabel("")
        self.errorLabel = QLabel("")
        
        # bottom
        self.Playing = QLabel("Playing: (song)")
        self.musicSlider = QSlider(orientation=Qt.Horizontal)
        self.timePlaying = QLabel("X:XX / X:XX")
        self.prevSong = QPushButton("<")
        self.togglePlayback = QPushButton("||")
        self.nextSong = QPushButton(">")

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
        
        self.playButtons.addWidget(self.timePlaying)
        self.playButtons.addWidget(self.prevSong)
        self.playButtons.addWidget(self.togglePlayback)
        self.playButtons.addWidget(self.nextSong)
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

        self.lowVbox = QVBoxLayout()
        
        self.masterVbox.addLayout(self.topHbox, 70)
        self.masterVbox.addLayout(self.lowVbox, 30)
        
        self.setWidgets()
        self.setLayout(self.masterVbox)    
    
    
    def setEvents(self):
        self.choosePlaylist.currentTextChanged.connect(self.choose_playlist)
        self.createPlaylist.clicked.connect(self.create_playlist)
        self.addSong.clicked.connect(self.add_song)
        
        self.deletePlaylist.clicked.connect(lambda: self.delete_item("playlist"))
        self.deleteSong.clicked.connect(lambda: self.delete_item("song"))
        
        self.prevSong.clicked.connect(lambda: print("pass"))
        self.togglePlayback.clicked.connect(self.toggle_play_song)
        self.nextSong.clicked.connect(lambda: print("pass"))
    
    
    def toggle_play_song(self):
        self.warningLabel.setText("")
        try:
            chosenPlaylist = self.choosePlaylist.currentText()
            chosenSong = self.playlistView.currentItem().text()
            songUrl = os.path.join("playlists", chosenPlaylist, chosenSong)
        except:
            self.warningLabel.setText("bruh")
            return
        
        if not os.path.exists(songUrl):
            self.warningLabel(f"{songUrl} does not exist!")
            return
        
        if self.loadedSong is None or (self.loadedSong != QUrl.fromLocalFile(songUrl)):
            self.loadedSong = QUrl.fromLocalFile(songUrl)
            self.songPlayer.setMedia(QMediaContent(self.loadedSong))

        if not self.isPlaying:
            self.songPlayer.play()
            self.Playing.setText(f"Playing: {chosenSong.removesuffix(".mp3")}")
            self.togglePlayback.setText("|>")
        elif self.isPlaying:
            self.songPlayer.pause()
            self.togglePlayback.setText("||")
            
        self.isPlaying = not self.isPlaying
             
             
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
    
    
    def choose_playlist(self):
        playlist = self.choosePlaylist.currentText()
        self.update_song_list(playlist)
        
        
    def add_song(self):
        currentPlaylist = self.choosePlaylist.currentText()
        fullpath = os.path.join("playlists",currentPlaylist)
        self.AddSongWindow = AddSongsWidget(currentPlaylist)
        self.AddSongWindow.exec()
        songs = self.AddSongWindow.songs.split('\n')
        
        self.threadpool = QThreadPool()
        worker = DownloadSongs(songs, fullpath)
        worker.signals.progress.connect(lambda val: self.updateWarning(val, songs))
        worker.signals.error.connect(lambda song: self.errorLabel.setText(f"Couldn't download\n\"{song}\""))
        worker.signals.finished.connect(self.finishWarning)
        
        self.finished = False
        self.threadpool.start(worker)
        
    def updateWarning(self, val, songs):
        self.warningLabel.setText(f"Downloaded {val+1}/{len(songs)} songs...")
    
    def finishWarning(self, val):
        self.warningLabel.setText(f"Finished Downloading {val} songs!")
        self.update_song_list(self.choosePlaylist.currentText())
    
    def update_playlists(self):
        if not os.path.exists("playlists"):
            os.mkdir("playlists")
            self.warningLabel("Please create a playlist!")
            return
        playlists = [playlist for playlist in os.listdir("playlists") if os.path.isdir(os.path.join("playlists", playlist))]
        self.choosePlaylist.clear()
        self.choosePlaylist.addItems(playlists)
        if playlists is not None:
            self.update_song_list(playlists[0])

    def update_song_list(self, playlist):
        songs = [song for song in os.listdir(os.path.join("playlists", playlist)) if song.endswith(".mp3")]
        self.playlistView.clear()
        self.playlistView.addItems(songs)
        
        
    def delete_item(self, str):
        self.warningLabel.setText("")
        if str == "playlist":
            item = self.choosePlaylist.currentText()
        elif str == "song":
            try:
                item = self.playlistView.currentItem().text()
            except AttributeError:
                self.warningLabel.setText("Please choose a song!")
                return
        deleteWindow = DeleteDialog(str, item)
        deleteWindow.exec_()
        


def main():
    app = QApplication(sys.argv)
    main_window = MainWidget(sys.argv)
    main_window.show()
    app.exec_()


if __name__ == "__main__":
    main()