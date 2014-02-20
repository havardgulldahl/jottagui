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
# Copyright 2014 Håvard Gulldahl <havard@gulldahl.no>

# import stdlib
import sys, logging


# import jottalib
import jottalib, jottalib.JFS, jottalib.jfstree, jottalib.qt


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
        item = idx.internalPointer()
        print 'double cliked: %s, %s' % (item.path, repr(item))
        if isinstance(item, (jottalib.JFS.JFSMountPoint, jottalib.JFS.JFSFolder)):
            logging.debug("lets change path: %s" % item.path)
            self.jottaModel.jfsChangePath(item.path)

    def showJottaDetails(self, idx):
        # some item was single clicked/selected, show details
        # itempath = unicode(idx.data(QtCore.Qt.UserRole).toString())
        item = idx.internalPointer()
        print 'selected: %s' % item.path
        coverPix = QtGui.QPixmap()
        coverPix.loadFromData(item.thumb())
        # return coverPix.scaled(200,200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.ui.detailsPix.setPixmap(coverPix)
        self.ui.detailsText.setText("""<b>Name</b>: %s<br><b>Size:</b> %s""" % (item.name, item.size))

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