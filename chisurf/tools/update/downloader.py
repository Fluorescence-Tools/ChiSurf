from __future__ import annotations

import os
import sys
import urllib

from PyQt5 import QtCore, QtWidgets, uic

import chisurf.settings as mfm


class UpdateDialog(QtWidgets.QWidget):

    def __init__(
            self,
            parent: QtWidgets.QLayout = None,
            installed_version: str = None
    ):
        super().__init__(parent=parent)
        uic.loadUi(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "update_form.ui"
            ),
            self
        )

        online_version = None
        self.filedownloadthread = None
        self.download_file = None

        request = urllib.Request(chisurf.settings.cs_settings['updates']['check_version_url'])
        request.add_header('Pragma', 'no-cache')
        try:
            content = urllib.build_opener().open(request)
            online = content.readlines()
            online_version = online[0].strip()
            self.download_file = online[1].strip()

            self.lineEdit_2.setText(online_version)
        except:
            print("Problems getting update.")
        #online = urllib.urlopen().readlines()

        if installed_version is None:
            installed_version = chisurf.settings.cs_settings['version']

        self.lineEdit.setText(installed_version)
        changes = urllib.urlopen(chisurf.settings.cs_settings['updates']['changes']).read()
        self.textEdit.setText(changes)
        self.actionDownloadUpdate.triggered.connect(self.start_download)

        if online_version is not None:
            if chisurf.settings.cs_settings['updates']['check_for_updates'] and installed_version < online_version:
                self.show()

    def start_download(self):
        target = chisurf.widgets.save_file(
            working_path="setup_current.exe",
            file_type='exe (*.exe)'
        )
        self.filedownloadthread = FileDownloadThread(progbar=self.progressBar, url=self.download_file, target=target)
        self.filedownloadthread.signal.connect(self.update)
        self.filedownloadthread.start()

    def update(self, percent):
        self.progressBar.setValue(percent)


class FileDownloadThread(QtCore.QThread):
    signal = QtCore.pyqtSignal()

    def __init__(self, progbar, url, target):
        super().__init__()
        self._url = url
        self._target = target
        self.progbar = progbar

    def run(self):
        url = self._url
        outputfile = self._target

        def reporthook(blocknum, blocksize, totalsize):
            readsofar = blocknum * blocksize
            percent = 0
            if totalsize > 0:
                percent = readsofar * 1e2 / totalsize
                s = "\r%5.1f%% %*d / %d" % (
                    percent, len(str(totalsize)), readsofar, totalsize)
                sys.stderr.write(s)
                if readsofar >= totalsize:
                    sys.stderr.write("\n")
            else:
                sys.stderr.write("read %d\n" % (readsofar,))
            self.signal.emit(int(percent))

        proxy = urllib.ProxyHandler({'http': "myproxy"})
        opener = urllib.build_opener(proxy)
        urllib.install_opener(opener)
        urllib.urlretrieve(url, outputfile, reporthook)
