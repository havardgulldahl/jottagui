#!/usr/bin/env python2.7
# -*- encoding: utf-8 -*-
#
# This file is part of jottafs.
#
# jottafs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# jottafs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jottafs.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2014-2015 Håvard Gulldahl <havard@gulldahl.no>

# import stdlib
import sys, logging
logging.captureWarnings(True)


# import jottalib
import jottalib, jottalib.JFS, jottalib.qt


# import pyqt4
from PyQt4 import QtGui, QtCore

# import jottagui
from ui.main_ui import Ui_MainWindow

class LoginDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        super(LoginDialog, self).__init__(parent)

        layout = QtGui.QHBoxLayout(self)

        self.username = QtGui.QLineEdit(self)
        layout.addWidget(self.username)
        self.password = QtGui.QLineEdit(self)
        self.password.setEchoMode(QtGui.QLineEdit.PasswordEchoOnEdit )
        layout.addWidget(self.password)

        # OK and Cancel buttons
        self.buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        layout.addWidget(self.buttons)

    # get current date and time from the dialog
    def userpass(self):
        return (self.username.text(), self.password.text())

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getLogin(parent = None):
        dialog = LoginDialog(parent)
        dialog.buttons.accepted.connect(dialog.accept)
        dialog.buttons.rejected.connect(dialog.reject)
        result = dialog.exec_()
        return (dialog.userpass(), result == QtGui.QDialog.Accepted)


class Downloader(QtCore.QObject):
    "Threaded class to do our download while not blocking the gui"
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)

    def __init__(self, jottafile, localpath, parent=None):
        super(Downloader, self).__init__(parent)
        self.jottafile = jottafile
        self.localpath = localpath

    def stream(self):
        "convenience method to stream (save) a jottafile to localpath"
        with open(self.localpath, 'w+b') as f:
            total = float(self.jottafile.size)
            current = 0.0
            for c in self.jottafile.stream():
                f.write(c)
                current = current + len(c)
                progress = current/total*100
                self.progress.emit(progress)
                logging.debug('wrote chunk of %s, %s/%s', self.jottafile.name, current, total)
        self.finished.emit()



class JottaGui(QtGui.QMainWindow):
    loginStatusChanged = QtCore.pyqtSignal(bool)
    downloading = QtCore.pyqtSignal(bool) # a boolean flag to indicate download activity
    progress = QtCore.pyqtSignal(int)     # an integer (0-100) to indicate progress
    notification = QtCore.pyqtSignal(unicode)  # a string with noteworthy content

    def __init__(self, app, parent=None):
        super(JottaGui, self).__init__(parent)
        self.app = app
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.jottaModel = None
        self.loginStatusChanged.connect(self.populateDevices)
        self.ui.listDevices.currentIndexChanged[str].connect(self.populateJottaRoot)
        __preview = QtGui.QWidget()
        __layout = QtGui.QVBoxLayout()
        __thumbnail = QtGui.QLabel(__preview)
        __thumbnail.setObjectName('thumbnail')
        __layout.addWidget(__thumbnail)
        __details = QtGui.QLabel(__preview)
        __details.setObjectName('details')
        __layout.addWidget(__details)
        self.btnget = QtGui.QPushButton('Get')
        __layout.addWidget(self.btnget)
        __preview.setLayout(__layout)
        self.btnget.clicked.connect(self.get)
        self.ui.jottafsView.setPreviewWidget(__preview)
        #self.ui.statusbar = QtGui.QStatusBar(self.ui.centralwidget)
        # self.ui.jottafsView.clicked.connect(self.populateChildNodes)
        # self.ui.jottafsView.clicked.connect(self.showJottaDetails)
        self.ui.actionLogin.triggered.connect(self.showModalLogin)
        self.downloading.connect(self.downloadActive)
        self.progress.connect(lambda x: self.ui.progressBar.setValue(x))
        self.notification.connect(lambda x: self.notify(x))

    def login(self, username, password):
        try:
            self.jfs = jottalib.JFS.JFS(username, password)
            self.loginStatusChanged.emit(True)
        except Exception as e:
            logging.exception(e)
            self.loginStatusChanged.emit(False)

    def showModalLogin(self):
        usernamepassword, ok = LoginDialog.getLogin()
        if ok:
            u,p = usernamepassword
            logging.debug('Got login %s', u)
            self.login(u, p)


    def populateChildNodes(self, idx, oldidx):
        logging.debug('populateChildNodes(self, %s, %s)' % (idx, oldidx))
        self.jottaModel.populateChildNodes(idx) # pass it on to model to expand children
        self.showJottaDetails(idx)

    def populateDevices(self, loggedin):
        # devices = self.jfs.devices()
        if not loggedin:
            self.ui.listDevices.clear()
        else:
            self.ui.listDevices.addItems([d.name for d in self.jfs.devices])
            self.populateJottaRoot(unicode(self.ui.listDevices.currentText()))

    def populateJottaRoot(self, device):
        self.jottaModel = jottalib.qt.JFSModel(self.jfs, '/%s' % device)
        self.ui.jottafsView.setModel(self.jottaModel)
        self.ui.jottafsView.selectionModel().currentChanged.connect(self.populateChildNodes)

    def showJottaDetails(self, idx):
        # some item was single clicked/selected, show details
        self.progress.emit(0)
        item = self.jottaModel.itemFromIndex(idx)
        logging.debug('selected: %s' % unicode(item.text()))
        __details = self.ui.jottafsView.previewWidget()
        if isinstance(item, jottalib.qt.JFSFileNode):
            s = """<b>Name</b>: %s<br><b>Size:</b> %s<br>
                   <b>Created</b>: %s<br><b>Modified</b>:%s""" % \
                                                             (item.obj.name, sizeof_fmt(item.obj.size),
                                                              item.obj.created, item.obj.modified)
        else:
            s = """<b>Name</b>: %s<br>"""  % (item.obj.name,)
        __details.findChild(QtGui.QLabel, 'details').setText(s)
        __preview = __details.findChild(QtGui.QLabel, 'thumbnail')
        __coverPix = QtGui.QPixmap()
        if isinstance(item, jottalib.qt.JFSFileNode) and item.obj.is_image():
            logging.debug('%s is an image, get thumb' % item.obj.name)
            __coverPix.loadFromData(item.obj.thumb(jottalib.JFS.JFSFile.MEDIUMTHUMB))
        __preview.setPixmap(__coverPix)

    def get(self):
        "Download current selected resource"
        # TODO find dlfolder based on content.
        # QDesktopServices::DesktopLocation	0	Returns the user's desktop directory.
        # QDesktopServices::DocumentsLocation	1	Returns the user's document.
        # QDesktopServices::FontsLocation	2	Returns the user's fonts.
        # QDesktopServices::ApplicationsLocation	3	Returns the user's applications.
        # QDesktopServices::MusicLocation	4	Returns the users music.
        # QDesktopServices::MoviesLocation	5	Returns the user's movies.
        # QDesktopServices::PicturesLocation	6	Returns the user's pictures.
        # QDesktopServices::TempLocation	7	Returns the system's temporary directory.
        # QDesktopServices::HomeLocation 8	Returns the user's home directory.

        dlfolder = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.PicturesLocation)
        selected = [self.jottaModel.itemFromIndex(idx) for idx in self.ui.jottafsView.selectedIndexes()]
        self.progress.emit(0)
        self.threads = []
        self.downloads = []
        self.downloading.emit(False)
        for item in selected:
            if isinstance(item, jottalib.qt.JFSFileNode):
                logging.debug('downloading %s ...' % item.obj.name)
                base,ext = os.path.splitext(item.obj.name)
                p = os.path.join(dlfolder, '%s-%s%s' % (base, item.obj.uuid, ext))
                T = QtCore.QThread()
                down = Downloader(item.obj, p)
                down.moveToThread(T)
                down.finished.connect(T.quit)
                down.finished.connect(lambda: self.notify("%s downloaded to %s" % (item.obj.name, p)))
                down.finished.connect(lambda: self.downloading.emit(False))
                down.progress.connect(self.ui.progressBar.setValue)
                T.started.connect(down.stream)
                self.downloading.emit(True)
                T.start()
                self.threads.append(T)
                self.downloads.append(down)


    def notify(self, msg):
        "Popup a non-intrusive textual notification"
        logging.info(msg)
        if not QtGui.QSystemTrayIcon.supportsMessages():
            return False

        pop = QtGui.QSystemTrayIcon()
        pop.showMessage(u'JottaGui', msg)

    def downloadActive(self, boolean):
        "Called when a download is active and when it finishes"
        self.btnget.setText('Downloading...' if boolean else 'Get')
        self.btnget.setDisabled(boolean)

    def run(self, app):
        self.show()
        sys.exit(app.exec_())

    def setLanguage(self, language):
        if self.translator is not None:
            self.app.removeTranslator(self.translator)
        else:
            self.translator = Core.QTranslator(self.app)
        print "loading translation: odometer_%s" % language
        self.translator.load(':data/translation_%s' % language)
        self.app.installTranslator(self.translator)
        # also for qt strings
        if self.translatorQt is not None:
            self.app.removeTranslator(self.translatorQt)
        else:
            self.translatorQt = Core.QTranslator(self.app)
        print "loading Qttranslation: qt_%s" % language
        self.translatorQt.load(':data/qt_%s' % language)
        self.app.installTranslator(self.translatorQt)



def rungui(argv, username, password):
    if sys.platform == 'win32':
        # default win32 looks awful, make it pretty
        # docs advise to do this before QApplication() is started
        QtGui.QApplication.setStyle("cleanlooks")
    app = QtGui.QApplication(argv)
    if sys.platform == 'win32':
        def setfont(fontname):
            app.setFont(QtGui.QFont(fontname, 9))
            return unicode(app.font().toString()).split(',')[0] == fontname
        # default win32 looks awful, make it pretty
        for z in ['Lucida Sans Unicode', 'Arial Unicode MS', 'Verdana']:
            if setfont(z): break
    o = JottaGui(app)
    if username is not None and password is not None:
        o.login(username, password)
    o.run(app)


def sizeof_fmt(num, use_kibibyte=True):
    # from http://stackoverflow.com/a/18289245
    base, suffix = [(1000.,'B'),(1024.,'iB')][use_kibibyte]
    for x in ['B'] + map(lambda x: x+suffix, list('kMGTP')):
        if -base < num < base:
            return "%3.1f %s" % (num, x)
        num /= base
    return "%3.1f %s" % (num, x)

if __name__ == '__main__':
    import os, netrc
    try:
        n = netrc.netrc()
        username, account, password = n.authenticators('jottacloud') # read .netrc entry for 'machine jottacloud'
    except:
        username = os.environ.get('JOTTACLOUD_USERNAME', None)
        password = os.environ.get('JOTTACLOUD_PASSWORD', None)

    #logging.basicConfig(level=logging.DEBUG)
    rungui(sys.argv, username, password)
