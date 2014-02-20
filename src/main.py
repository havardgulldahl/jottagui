#!/usr/bin/env python2.7

# import stdlib
import sys


# import jottalib
import jottalib, jottalib.jfstree, jottalib.qt


# import pyqt4
from PyQt4 import QtGui, QtCore

# import jottagui
from ui.main_ui import Ui_MainWindow

class JottaGui(QtGui.QMainWindow):
    loginStatusChanged = QtCore.pyqtSignal(bool)

    def __init__(self, app, parent=None):
        super(JottaGui, self).__init__(parent)
        self.app = app
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.jottaModel = None
        self.loginStatusChanged.connect(self.populateDevices)
        self.ui.comboDevices.currentIndexChanged[str].connect(self.populateJottaRoot)
        self.ui.listItems.doubleClicked.connect(self.populateJottaItems)
        self.ui.listItems.clicked.connect(self.showJottaDetails)

    def login(self, username, password):
        try:
            self.jfs = jottalib.jfstree.JFSTree(username, password)
            self.loginStatusChanged.emit(True)
        except Exception as e:
            print e
            self.loginStatusChanged.emit(False)

    def populateDevices(self):
        devices = self.jfs.devices()
        self.ui.comboDevices.addItems([d.name for d in devices])
        self.populateJottaRoot(unicode(self.ui.comboDevices.currentText()))

    def populateJottaRoot(self, device):
        self.jottaModel = jottalib.qt.JFSModel(self.jfs, '/%s' % device)
        self.ui.listItems.setModel(self.jottaModel)

    def populateJottaItems(self, idx):
        # some item was double clicked, enter it if it is a folder
        itempath = unicode(idx.data(QtCore.Qt.UserRole).toString())
        print 'double cliked: %s' % itempath
        self.ui.detailsText.setText(itempath)

    def showJottaDetails(self, idx):
        # some item was single clicked/selected, show details
        itempath = unicode(idx.data(QtCore.Qt.UserRole).toString())
        print 'selected: %s' % itempath

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
    o.login(username, password)
    o.run(app)

if __name__ == '__main__':
    import os
    rungui(sys.argv, os.environ['JOTTACLOUD_USERNAME'], os.environ['JOTTACLOUD_PASSWORD'])