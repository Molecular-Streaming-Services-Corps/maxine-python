#!/usr/bin/env python
import wx
import os
import subprocess
import platform

import constants

CONSOLE_NAME = 'Kent'

class MLFrame(wx.Frame):
    """
    An empty Frame for Maxine Launcher
    """
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super().__init__(*args, **kw)

        # create a panel in the frame
        self.panel = wx.Panel(self)
        
        self.pd_btn = wx.Button(self.panel, -1, "Open poredata") 
        self.pd_btn.Bind(wx.EVT_BUTTON, self.OpenPoredata) 
        
        self.video_btn = wx.Button(self.panel, -1, "Choose background video")
        self.video_btn.Bind(wx.EVT_BUTTON, self.ChooseVideo)
        
        levels = []
        for lvl in range(1, constants.NUM_LEVELS + 1):
            levels.append(str(lvl))
        
        self.levels_box = wx.ListBox(self.panel, choices = levels, style = wx.LB_SINGLE)
        self.levels_box.Bind(wx.EVT_LISTBOX, self.ChooseLevel)
        
        modes = ["Standalone", "Prerecorded", "Live"]
        
        self.mode_box = wx.ListBox(self.panel, choices = modes, style = wx.LB_SINGLE)
        self.mode_box.Bind(wx.EVT_LISTBOX, self.ChooseMode)
        
        self.launch_btn = wx.Button(self.panel, -1, "Launch Maxine")
        self.launch_btn.Bind(wx.EVT_BUTTON, self.Launch)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany([self.mode_box, self.pd_btn, 
            self.video_btn, self.levels_box, self.launch_btn])
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
        
        if self.video is not None:
            arguments += ['--video', self.video]
        
        live = False
        
        if self.mode == 'Standalone':
            pass
        elif self.mode == 'Prerecorded' and self.data_dir is not None:
            arguments += ['--datadir', self.data_dir]
        elif self.mode == 'Live':
            arguments += ['--live', CONSOLE_NAME]
            live = True
    
        if platform.system() == 'Windows':
            command = ["python", "maxine.py"]
        elif platform.system() == 'Linux':
            command = ["python3", "maxine.py"]

        if not live:
            subprocess.Popen(command + arguments)
        else:
            subprocess.Popen(command + arguments + ['--player', 'console'])
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

