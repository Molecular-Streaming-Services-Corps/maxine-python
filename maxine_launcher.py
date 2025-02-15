#!/usr/bin/env python
import wx
import os
import subprocess
import platform

import constants

DEFAULT_CONSOLE_NAME = 'Kent'

class MLFrame(wx.Frame):
    """
    An empty Frame for Maxine Launcher
    """
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super().__init__(*args, **kw)

        # create a panel in the frame
        self.panel = wx.Panel(self)
        
        # Data options section
        
        self.data_options_label = wx.StaticText(self.panel, label = "Data options")
        
        self.dataview = wx.CheckBox(self.panel, label = "DataView")
        
        self.modes_label = wx.StaticText(self.panel, label = "Choose data mode")
        
        modes = ["Standalone", "Prerecorded", "Live"]
        
        self.mode_box = wx.ListBox(self.panel, choices = modes, style = wx.LB_SINGLE)
        self.mode_box.Bind(wx.EVT_LISTBOX, self.ChooseMode)
        
        self.pd_btn = wx.Button(self.panel, -1, "Open poredata") 
        self.pd_btn.Bind(wx.EVT_BUTTON, self.OpenPoredata) 
        
        self.start_at_label = wx.StaticText(self.panel, label = "Start at time (in seconds)")
        
        self.start_at_box = wx.TextCtrl(self.panel)
        
        self.console_label = wx.StaticText(self.panel, label = "Choose console")
        
        consoles = list(constants.MACS)
        self.console_box = wx.ListBox(self.panel, choices = consoles, style = wx.LB_SINGLE)
        
        # Game options section
        
        self.game_options_label = wx.StaticText(self.panel, label = "Game options")
        
        self.video_btn = wx.Button(self.panel, -1, "Choose background video")
        self.video_btn.Bind(wx.EVT_BUTTON, self.ChooseVideo)
        
        self.levels_label = wx.StaticText(self.panel, label = "Choose level")
        
        levels = []
        for lvl in range(1, constants.NUM_LEVELS + 1):
            levels.append(str(lvl))
        
        self.levels_box = wx.ListBox(self.panel, choices = levels, style = wx.LB_SINGLE)
        self.levels_box.Bind(wx.EVT_LISTBOX, self.ChooseLevel)
                
        self.zombies_label = wx.StaticText(self.panel,
            label = "Choose number of zombies that appear with each spike")
        self.snakes_label = wx.StaticText(self.panel, label = "Snakes")
        self.ghosts_label = wx.StaticText(self.panel, label = "Ghosts")
        
        self.zombies_box = wx.TextCtrl(self.panel)
        self.snakes_box = wx.TextCtrl(self.panel)
        self.ghosts_box = wx.TextCtrl(self.panel)
        
        self.doors_label = wx.StaticText(self.panel,
            label = "Choose the number of doors that appear with each spike")
        self.doors_box = wx.TextCtrl(self.panel)
        
        self.launch_btn = wx.Button(self.panel, -1, "Launch Maxine")
        self.launch_btn.Bind(wx.EVT_BUTTON, self.Launch)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany([self.data_options_label, self.dataview,
            self.modes_label, self.mode_box, self.pd_btn,
            self.start_at_label, self.start_at_box,
            self.console_label, self.console_box,
            self.game_options_label,
            self.video_btn, self.levels_label, self.levels_box,
            self.zombies_label, self.zombies_box,
            self.snakes_label, self.snakes_box,
            self.ghosts_label, self.ghosts_box,
            self.doors_label, self.doors_box,
            self.launch_btn])
        self.panel.SetSizer(sizer)
        
        self.data_dir = None
        self.level = 1
        self.video = None
        self.mode = "Standalone"

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OpenPoredata(self, event):
        self.data_dir = choose_data_dir(self)

    def ChooseVideo(self, event):
        self.video = choose_video(self)

    def ChooseLevel(self, event):
        lvl = int(event.GetEventObject().GetStringSelection())
        self.level = lvl

    def ChooseMode(self, event):
        mode = event.GetEventObject().GetStringSelection()
        self.mode = mode

    def Launch(self, event):
        arguments = []
        
        arguments += ['--level', str(self.level)]
        
        # These shouldn't be used with DataView
        if self.video is not None:
            arguments += ['--video', self.video]
        
        sab_text = self.start_at_box.GetLineText(0)
        if (sab_text != ''):
            arguments += ['--start-at', sab_text]
        
        if (self.zombies_box.GetLineText(0) != '' and
                self.snakes_box.GetLineText(0) != '' and
                self.ghosts_box.GetLineText(0) != ''):
            zombies = int(self.zombies_box.GetLineText(0))
            snakes = int(self.snakes_box.GetLineText(0))
            ghosts = int(self.ghosts_box.GetLineText(0))
            
            ratio = str((zombies, snakes, ghosts))
            
            arguments += ['--monster-ratio', ratio]
        
        if self.doors_box.GetLineText(0) != '':
            doors = int(self.doors_box.GetLineText(0))
            
            arguments += ['--doors', str(doors)]
        
        # These should be used with DataView
        dataview = self.dataview.GetValue()
        if dataview:
            arguments += ['--dataview']
        
        live = False
        
        if self.mode == 'Standalone':
            pass
        elif self.mode == 'Prerecorded' and self.data_dir is not None:
            arguments += ['--datadir', self.data_dir]
        elif self.mode == 'Live':            
            selection = self.console_box.GetSelection()
            if selection == -1:
                console_name = DEFAULT_CONSOLE_NAME
            else:
                console_name = self.console_box.GetString(selection)
            
            arguments += ['--live', console_name]
            live = True
    
        if platform.system() == 'Windows':
            command = ["python", "maxine.py"]
        elif platform.system() == 'Linux':
            command = ["python3", "maxine.py"]

        if not live:
            subprocess.Popen(command + arguments)
        else:
            subprocess.Popen(command + arguments + ['--player', 'console'])
            # We don't want the Maxine game with DataView
            if not dataview:
                subprocess.Popen(command + arguments + ['--player', 'maxine'])
    
app = None
def setup_UI():
    app = wx.App()
    frame = MLFrame(None, title='MRGames Maxine Launcher')
    frame.Show()
    
    app.MainLoop()

def choose_data_dir(frame):
    with wx.FileDialog(frame, "Open poredata.bin file", wildcard="poredata.bin|poredata.bin",
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return None     # the user changed their mind

        # Return the directory where poredata.bin was found
        pathname = fileDialog.GetPath()
        return os.path.dirname(pathname)

def choose_video(frame):
    with wx.FileDialog(frame, "Open video file", 
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
        
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return None
            
        pathname = fileDialog.GetPath()
        return pathname

if __name__ == '__main__':
    setup_UI()

