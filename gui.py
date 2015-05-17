# The MIT License (MIT)

# Copyright (c) 2015 Joel Robichaud

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import stat
import time
import wx

from wx.lib.delayedresult import startWorker
from ObjectListView import ObjectListView, ColumnDefn

class MyFileDropTarget(wx.FileDropTarget):
    """Custom file drop target."""

    def __init__(self, window):
        """Constructor."""

        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        """Files dropped event handler."""

        # Expand folders recursively
        expanded_filenames = []
        for file in filenames:
            if os.path.isdir(file):
                for root, dirnames, filenames in os.walk(file):
                    expanded_filenames.extend([os.path.join(root, file) for file in filenames])
            else:
                expanded_filenames.append(file)

        # Filter out unsupported extensions
        expanded_filenames = [file for file in expanded_filenames
                              if os.path.splitext(file)[-1].lower() == ".wav"]

        self.window.updateDisplay(expanded_filenames)

class FileInfo(object):
    """File information model."""

    def __init__(self, path, date_created, date_modified, size):
        """Constructor."""

        self.name = os.path.basename(path)
        self.path = path
        self.date_created = date_created
        self.date_modified = date_modified
        self.size = size

class MainPanel(wx.Panel):
    """Polyscribe main panel."""

    def __init__(self, parent, converter):
        """Constructor."""

        wx.Panel.__init__(self, parent=parent)
        self.converter = converter
        self.file_list = []

        # Element creation
        file_drop_target = MyFileDropTarget(self)
        self.olv = ObjectListView(self, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.olv.SetDropTarget(file_drop_target)
        self.olv.SetEmptyListMsg("Drag files to convert")
        self.olv.evenRowsBackColor = "#ffffff"
        self.olv.oddRowsBackColor = "#efefef"
        self.setFiles()

        self.btn = wx.Button(self, wx.ID_ANY, "Convert")

        # Event bindings
        self.Bind(wx.EVT_BUTTON, self.OnConvert, self.btn)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUp)

        # Element positioning
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.olv, 1, wx.EXPAND)
        sizer.Add(self.btn, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, 10)
        self.SetSizer(sizer)

    def OnConvert(self, evt):
        """Convert button event handler."""

        if self.converter and len(self.file_list):
            # Prompt the user to select a destination for the converted file
            saveDialog = wx.FileDialog(self, defaultDir=os.getcwd(),
                                        defaultFile="output.pdf",
                                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            if saveDialog.ShowModal() == wx.ID_OK:
                # Start the conversion process in a different thread
                outputPath = saveDialog.GetPath().replace(".pdf", "")
                startWorker(self.OnConversionCompleted, self.convertWorker,
                            wargs=([file.path for file in self.file_list], outputPath))

                # Show an indeterminate progress bar while the conversion is happening in the background.
                self.progressComplete = False
                self.keepGoing = True
                progressDialog = wx.ProgressDialog("Converting to sheet music",
                                                   "This may take a while...",
                                                   parent=self,
                                                   style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT)

                while self.keepGoing and not self.progressComplete:
                    self.keepGoing = progressDialog.Pulse()[0]
                    wx.MilliSleep(30)
                progressDialog.Destroy()

                if os.path.exists(outputPath):
                    os.remove(outputPath)

    def OnKeyUp(self, evt):
        """Keyboard keyup event handler."""

        selected_objs = self.olv.GetSelectedObjects()

        # The delete key can be used to removed currently selected rows
        if evt.GetKeyCode() == wx.WXK_DELETE and selected_objs:
            self.removeFiles(selected_objs)

        evt.Skip()

    def OnConversionCompleted(self, result):
        """Conversion worker event handler."""

        if result.get():
            self.progressComplete = True

    def convertWorker(self, filenames, destination):
        """Conversion worker."""

        for progress in self.converter.convert(filenames, destination):
            if not self.keepGoing:
                return False
        return True

    def updateDisplay(self, file_list):
        """Format and diplay file information inside the ObjectListView."""

        for path in file_list:
            file_stats = os.stat(path)
            creation_time = time.strftime("%m/%d/%Y %I:%M %p",
                                          time.localtime(file_stats[stat.ST_CTIME]))
            modified_time = time.strftime("%m/%d/%Y %I:%M %p",
                                          time.localtime(file_stats[stat.ST_MTIME]))
            file_size = file_stats[stat.ST_SIZE]
            if file_size > 1024:
                file_size = file_size / 1024.0
                if file_size > 1024:
                    file_size = file_size / 1024.0
                    file_size = "%.2f MB" % file_size
                else:
                    file_size = "%.2f KB" % file_size
            else:
                file_size = "%i bytes" % file_size

            self.file_list.append(FileInfo(path,
                                           creation_time,
                                           modified_time,
                                           file_size))

        self.olv.SetObjects(self.file_list)

    def removeFiles(self, file_list):
        """Remove files and update the ObjectListView."""

        for file in file_list:
            self.file_list.remove(file)
        self.olv.SetObjects(self.file_list)

    def setFiles(self):
        """Initialize the ObjectListView."""

        self.olv.SetColumns([ColumnDefn("Name", "left", 220, "name"),
                             ColumnDefn("Date modified", "left", 150, "date_modified"),
                             ColumnDefn("Date created", "left", 150, "date_created"),
                             ColumnDefn("Size", "left", 100, "size")])
        self.olv.SetObjects(self.file_list)

class MainFrame(wx.Frame):
    """Polyscribe main frame."""

    def __init__(self, converter=None):
        """Constructor."""

        wx.Frame.__init__(self, None, title="Polyscribe", size=(650,500))
        panel = MainPanel(self, converter)

        menu = wx.MenuBar()
        self.SetMenuBar(menu)

        self.Show()

if __name__ == "__main__":
    # Test code
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
