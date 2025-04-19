import customtkinter as ctk
import tkinter as tk
import ttkbootstrap as ttk
import math
import os
import pygame
import yt_dlp
from mutagen.mp3 import MP3

pygame.mixer.init()
music = pygame.mixer.music
ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',  # Optional: 128, 192, 256, 320
    }],
    'outtmpl': '%(title)s.%(ext)s',  # customize output folder & name
    'quiet': False,
    'playlistened': 1,
    'ignoreerrors' : True,
}

class SongWindow(ttk.Window):
    def __init__(self):
        super().__init__()
        self.geometry('500x300')
        self.resizable(0, 0)
        self.title('TKinter thing')
        self.input = tk.StringVar()
        self.submitted = tk.BooleanVar(value=False)
        self.setWidgets()

    def setWidgets(self):
        self.Label = ttk.Label(master=self, text="Add Youtube Link(s)/Playlist(s)", font=('JetBrainsMono NF', 10), background="#FFFFFF")
        self.Label.pack(pady=10)

        self.Frame = ttk.Frame(master=self, width=450, height=200)
        self.Text = tk.Text(master=self.Frame)

        self.Frame.pack()
        self.Frame.pack_propagate(False)
        self.Text.pack()

        self.Button = ttk.Button(master=self, text='Okay', command=self.store_input)
        self.Button.pack(pady=10)

    def store_input(self):
        text = self.Text.get("1.0", tk.END).strip()
        self.input.set(text)
        self.submitted.set(value=True)
        self.destroy()

    def get_input(self):
        return self.input.get() if self.input.get() else ""
    
class PlayListWindow(ttk.Window):
    def __init__(self):
        super().__init__()
        self.geometry('450x100')
        self.resizable(0, 0)
        self.title('TKinter thing')
        self.input = tk.StringVar()
        self.submitted = tk.BooleanVar(value=False)
        self.pack_propagate(False)
        self.setWidgets()

    def setWidgets(self):
        self.Label = ttk.Label(master=self, text="Enter Playlist Name", font=('JetBrainsMono NF', 10), background="#FFFFFF")
        self.Label.pack()

        self.Entry = ttk.Entry(master=self, width=50)
        self.Entry.pack_propagate(False)
        self.Entry.pack(pady=5)

        self.Button = ttk.Button(master=self, text='Okay', command=self.store_input)
        self.Button.pack(pady=10)

    def store_input(self):
        text = self.Entry.get().strip()
        self.input.set(text)
        self.submitted.set(value=True)
        self.destroy()

    def get_input(self):
        return self.input.get() if self.input.get() else ""

class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__()
        self.geometry('450x600')
        self.resizable(0,0)
        self.title('YT Music Shit')
        self.TopWidgets()
        self.MiddleWidget()
        self.BottomWidgets()
        self.configure(background="#212121")
        self.input = ttk.StringVar()
        self.currentlyPlaying = None
        self.songLength = None
        self.userSliderMove = False
        self.offset = 0
        self.paused = False
        self.openedDialog = False
        self.isLoop = False
    
    def TopWidgets(self):
        # Top Frame
        self.style.configure('TopFrame.TFrame', background="#2A2A2A")
        self.TopFrame = ttk.Frame(master=self, width=400, height=50, style='TopFrame.TFrame')
        self.TopFrame.pack_propagate(False)
        self.TopFrame.pack(pady=10)

        # Top Frame Playlists
        try:
            playlists = [os.path.basename(f.path) for f in os.scandir(f"playlists") if f.is_dir()]
        except FileNotFoundError:
            os.mkdir("playlists")
            playlists = []
        self.PlaylistString = tk.StringVar(value='Choose or Create a Playlist...')
        self.Playlists = ttk.Combobox(master=self.TopFrame, state="readonly", values=playlists, textvariable=self.PlaylistString, width=27)
        self.Playlists.pack(side='left', padx=5, pady=5)
        self.Playlists.pack_propagate(False)
        self.Playlists.bind('<<ComboboxSelected>>', self.refreshSongList)

        # Top Frame Buttons
        self.PDialog = ""
        self.style.configure('TButton', font=("Espresso Dolce", 10))
        self.ButtonAddPlaylist = ttk.Button(master=self.TopFrame, text='Create Playlist')
        self.ButtonAddPlaylist['command'] = self.askPlaylist
        self.ButtonAddPlaylist.pack(side='left', padx=5, pady=1)

        self.SDialog = SongWindow
        self.SDialog = SongWindow.root = self
        self.ButtonAddSongs = ttk.Button(master=self.TopFrame, text="Add Song/s")
        self.ButtonAddSongs['command'] = lambda: self.askSong(self.Playlists.get())
        if self.Playlists.get() == "Choose or Create a Playlist...":
            self.ButtonAddSongs['state'] = 'disabled'
        self.ButtonAddSongs.pack(side='left',padx=5, pady=1)
    
    def MiddleWidget(self):
        # Middle Frame
        self.style.configure("MiddleFrame.TFrame", background="#2A2A2A")
        self.MiddleFrame = ttk.Frame(master=self, width=400, height=300, style="MiddleFrame.TFrame")
        self.MiddleFrame.pack_propagate(False)
        self.MiddleFrame.pack(pady=5)

        # Middle Tree View
        self.style.configure('Treeview', font=("Lucida Sans Unicode", 10), background="#2A2A2A", foreground='white', rowheight=25)
        self.style.map('Treeview', 
                background=[('selected', '#1f77b4')],
                foreground=[('selected', 'white')]) 
        self.TreeView = ttk.Treeview(master=self.MiddleFrame, selectmode='browse', show='headings')
        self.TreeView['columns'] = ('Songs',)
        self.TreeView.heading('Songs', text = 'Songs')
        self.TreeView.column('Songs', width=385, anchor='w')
        self.TreeView.pack(side='left', padx=5,pady=5)
        self.TreeView.bind('<Double-1>', lambda event: self.playSong())

        if len(self.TreeView.get_children()) > 10:
            self.TreeView.column('Songs', width=370)
            vertical_scrollbar = ttk.Scrollbar(self.MiddleFrame, orient="vertical", command=self.TreeView.yview, style='TScrollbar')
            vertical_scrollbar.pack(side="right", fill="y")
            self.TreeView.config(yscrollcommand=vertical_scrollbar.set)

    def BottomWidgets(self):
        # Bottom Frame
        self.style.configure('BottomFrame.TFrame', background="#2A2A2A")
        self.BottomFrame = ttk.Frame(master=self, width=400, height=150, style='BottomFrame.TFrame')
        self.BottomFrame.pack_propagate(False)
        self.BottomFrame.pack()

        # Label of Playing
        self.style.configure('Label', font=('JetBrainsMono NF', 15), background="#2A2A2A", foreground='white')
        self.PlayingLabel = ttk.Label(master=self.BottomFrame, text='SongName', style='Label')
        self.PlayingLabel.pack(padx=10,pady=5)

        # Slider
        self.style.configure('TScale', background="#2A2A2A", troughcolor="#444444", sliderlength=20, sliderthickness=15)
        self.scaleInt = ttk.IntVar(value=0)
        self.Slider = ttk.Scale(master=self.BottomFrame, length=375, from_ = 0, to = 100, command = self.userMoving, variable=self.scaleInt)
        self.Slider.pack()
        self.Slider.bind("<ButtonRelease-1>", self.on_slider_release)

        # Time Thing
        self.currPlaybackStr = tk.StringVar(value="0:00")
        self.currPlaybackLabel = ttk.Label(master=self.BottomFrame, textvariable=self.currPlaybackStr, style="Label", font=('JetBrainsMono NF', 10))
        self.currPlaybackLabel.pack(side='left', padx=10)

        self.songLengthStr = tk.StringVar(value="0:00")
        self.songLengthLabel = ttk.Label(master=self.BottomFrame, text="0:00", style="Label", font=('JetBrainsMono NF', 10))
        self.songLengthLabel.pack(side='right', padx=10)

        # BOTTOMER FRAME
        self.BottomestFrame = ttk.Frame(master=self, width=400, height=150, style='BottomFrame.TFrame')
        self.BottomestFrame.pack_propagate(False)
        self.BottomestFrame.pack()

        # SPACING FOR BUTTONS IM NOOB
        self.style.configure('Spacing.TFrame', background="#2A2A2A")
        self.SpacingFrame = ttk.Frame(master=self.BottomestFrame, width=45, style="Spacing.TFrame")
        self.SpacingFrame.pack(side='left')

        # The buttons
        self.ButtonPrev = ttk.Button(master=self.BottomestFrame, text="Prev Song", command= lambda: self.iterateSong(-1))
        self.ButtonTogglePause = ttk.Button(master=self.BottomestFrame, text="Play/Pause/Resume", command= self.playSong)
        self.ButtonNext = ttk.Button(master=self.BottomestFrame, text="Next Song", command= lambda: self.iterateSong(1))
        self.style.configure("Toggle.TButton", background="#555555", bordercolor="#555555", focusthickness=0)
        self.ButtonLoop = ttk.Button(master=self.BottomestFrame, text="loop", command=self.toggleLoop, style="Toggle.TButton")

        self.ButtonPrev.pack(side='left', padx=2)
        self.ButtonTogglePause.pack(side='left', padx=2)
        self.ButtonNext.pack(side='left', padx=2)
        self.ButtonLoop.pack(side='left', padx=2)

        if self.Playlists.get() == "Choose or Create a Playlist...":
            self.ButtonPrev['state'] = 'disabled'
            self.ButtonTogglePause['state'] = 'disabled'
            self.ButtonNext['state'] = 'disabled'

    # FUNCTIONS
    def toggleLoop(self):
        self.isLoop = not self.isLoop 
        if self.isLoop == False:
            self.style.configure("Toggle.TButton", background="#555555", bordercolor="#555555")
            print("noloop")
        else:
            self.style.configure("Toggle.TButton", background="#4582ec", bordercolor="#4582ec")
            print("loop")


    def iterateSong(self, value):
        currSelect = int(self.TreeView.selection()[0])
        if self.isLoop:
            value = 0
        if 1 <= currSelect + value <= len(self.TreeView.get_children()):
            self.stop_music_and_reset_slider()
            self.TreeView.focus(currSelect+value) 
            self.TreeView.selection_set(currSelect+value)
            self.playSong()
        elif len(self.TreeView.get_children()) < currSelect + value:
            self.stop_music_and_reset_slider()
            self.TreeView.focus('1') 
            self.TreeView.selection_set('1')
            self.playSong()
        elif currSelect + value < 1:
            self.stop_music_and_reset_slider()
            self.TreeView.focus(len(self.TreeView.get_children())) 
            self.TreeView.selection_set(len(self.TreeView.get_children()))
            self.playSong()
            

    def check_song_end(self):
        if not pygame.mixer.music.get_busy() and self.currentlyPlaying is not None and not self.paused:
            self.currentlyPlaying = None
            self.playSong()
        self.after(500, self.check_song_end)


    def userMoving(self, event):
        self.userSliderMove = True

    def playSong(self):
        self.openedDialog = False
        idSelected = self.TreeView.focus()
        self.TreeView.selection_set(idSelected)
        selected_item = self.TreeView.selection()[0]
        values = self.TreeView.item(selected_item, 'values')
        playlist = self.Playlists.get()
        relPath = "playlists/" + playlist + "/" +values[0]
        if not music.get_busy() and self.currentlyPlaying == None:
            music.load(relPath)
            self.currentlyPlaying = relPath
            music.play()
        elif self.currentlyPlaying == relPath:
            if music.get_busy():
                music.pause()
                self.paused = True
            else:
                music.unpause()
                self.paused = False
        elif self.currentlyPlaying != relPath:
            self.currentlyPlaying = relPath
            music.stop()
            music.load(relPath)
            music.play()
            self.slider_seek(0)
            self.offset = 0
            self.scaleInt.set(0)
        audio = MP3(relPath)
        length = audio.info.length 
        self.songLengthLabel['text'] = f"{math.floor(int(length)/60)}:{int(length)%60:02d}"
        self.PlayingLabel['text'] = values[0]
        self.Slider.config(to=length)
        self.songLength = length
        self.update_slider()


    def on_slider_release(self, event):
        seek_pos = int(float(self.scaleInt.get()))
        self.offset = seek_pos
        self.slider_seek(seek_pos)
        self.userSliderMove = False
        self.update_slider()


    def slider_seek(self, value):
        if music.get_busy():
            music.stop()
            music.load(self.currentlyPlaying)
            seek_pos = int(float(value))
            music.play(start=seek_pos)
            self.scaleInt.set(seek_pos)


    def update_slider(self):
        if music.get_busy() and self.userSliderMove == False:
            pos = self.offset + (music.get_pos()/1000)
            self.scaleInt.set(pos)
            curMinutes = math.floor(pos / 60)
            curSeconds = int(pos) % 60
            self.currPlaybackStr.set(f"{curMinutes}:{curSeconds:02d}")
            self.after(500, self.update_slider)
        if not music.get_busy() and self.currentlyPlaying != "" and not self.openedDialog and not self.paused:
            self.iterateSong(1)


    def askSong(self, dir):
        self.stop_music_and_reset_slider()
        self.openedDialog = True
        song = SongWindow()
        song.wait_window()
        if song.get_input() != "":
            for line in song.get_input().split('\n'):
                self.downloadUrl(line, dir)
        self.refreshSongList(self)
        self.openedDialog = False

    def askPlaylist(self):
        self.stop_music_and_reset_slider()
        self.openedDialog = True
        playlist = PlayListWindow()
        playlist.wait_window()
        if playlist.get_input() != "":
            os.mkdir(f'playlists\\{playlist.get_input()}')
            self.refreshPlaylists(playlist.get_input())
            self.ButtonAddSongs['state'] = 'enabled'
            self.ButtonPrev['state'] = 'enabled'
            self.ButtonTogglePause['state'] = 'enabled'
            self.ButtonNext['state'] = 'enabled'
        self.openedDialog = False

    def stop_music_and_reset_slider(self):
        if music.get_busy():
            music.stop()
        self.scaleInt.set(0)
        self.currPlaybackStr.set("0:00")
        self.songLengthLabel['text'] = "0:00" 
        self.offset = 0 
        self.currentlyPlaying = None 
        self.paused = False


    def refreshSongList(self, _=None):
        music.stop()
        self.scaleInt.set(0)
        chosenPlayist = self.Playlists.get()
        playlistSongs = [os.path.basename(f.path) for f in os.scandir(f"playlists\\{chosenPlayist}")]
        self.TreeView.delete(*self.TreeView.get_children())
        for i, song in enumerate(playlistSongs):
            self.TreeView.insert(parent='', index= tk.END, values = (f'{song}',), iid=i+1)
        
        self.TreeView.selection_set('1')
        self.TreeView.focus('1')
        self.ButtonAddSongs['state'] = 'enabled'
        self.ButtonPrev['state'] = 'enabled'
        self.ButtonTogglePause['state'] = 'enabled'
        self.ButtonNext['state'] = 'enabled'

    def refreshPlaylists(self, newPlaylist=""):
        playlists = [os.path.basename(f.path) for f in os.scandir(f"playlists") if f.is_dir()]
        self.Playlists['values'] = playlists
        self.TreeView.delete(*self.TreeView.get_children())
        if newPlaylist != "":
            self.Playlists.set(newPlaylist)

    def downloadUrl(self, url, dir):
        ydl_optsTemp = ydl_opts.copy()
        ydl_optsTemp['outtmpl'] = f"playlists/{dir}/%(title)s.%(ext)s"


        with yt_dlp.YoutubeDL(ydl_optsTemp) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                error_code = ydl.download([url])  # should be a list!
                return ydl.sanitize_info(info)['title']
            except yt_dlp.utils.DownloadError:
                return "Not a Valid Youtube URL!!!"

def main():
    window = MainWindow()
    window.mainloop()

if __name__ == "__main__":
    main()