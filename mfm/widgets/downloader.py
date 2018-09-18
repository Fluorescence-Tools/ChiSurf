from PyQt4 import QtGui, QtCore, uic
import sys
import urllib2
import urllib
import mfm


class UpdateDialog(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        uic.loadUi("mfm/ui/update_form.ui", self)
        online_version = None
        self.filedownloadthread = None
        self.download_file = None

        request = urllib2.Request(mfm.settings['updates']['check_version_url'])
        request.add_header('Pragma', 'no-cache')
        try:
            content = urllib2.build_opener().open(request)
            online = content.readlines()
            online_version = online[0].strip()
            self.download_file = online[1].strip()

            self.lineEdit_2.setText(online_version)
        except:
            print "Problems getting update."
        #online = urllib.urlopen().readlines()

        installed_version = mfm.settings['version']
        self.lineEdit.setText(installed_version)
        changes = urllib.urlopen(mfm.settings['updates']['changes']).read()
        self.textEdit.setText(changes)
        self.connect(self.actionDownloadUpdate, QtCore.SIGNAL('triggered()'), self.start_download)

        if online_version is not None:
            if mfm.settings['updates']['check_for_updates'] and installed_version < online_version:
                self.show()

    def start_download(self):
        target = mfm.widgets.save_file(working_path="setup_current.exe", file_type='exe (*.exe)')
        self.filedownloadthread = FileDownloadThread(progbar=self.progressBar, url=self.download_file, target=target)
        self.connect(self.filedownloadthread, QtCore.SIGNAL('signal'), self.update)
        self.filedownloadthread.start()

    def update(self, percent):
        self.progressBar.setValue(percent)


class FileDownloadThread(QtCore.QThread):

    def __init__(self, progbar, url, target):
        super(FileDownloadThread, self).__init__()
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
            self.emit(QtCore.SIGNAL('signal'), int(percent))

        proxy = urllib2.ProxyHandler({'http': "myproxy"})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)
        urllib.urlretrieve(url, outputfile, reporthook)
