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
        self.ui.listDevices.currentIndexChanged[str].connect(self.populateJottaRoot)
        __preview = QtGui.QWidget()
        __layout = QtGui.QVBoxLayout()
        __thumbnail = QtGui.QLabel(__preview)
        __thumbnail.setObjectName('thumbnail')
        __layout.addWidget(__thumbnail)
        __details = QtGui.QLabel(__preview)
        __details.setObjectName('details')
        __layout.addWidget(__details)
        __preview.setLayout(__layout)
        self.ui.jottafsView.setPreviewWidget(__preview)
        self.ui.getButton.clicked.connect(self.get)

        # self.ui.jottafsView.clicked.connect(self.populateChildNodes)
        # self.ui.jottafsView.clicked.connect(self.showJottaDetails)

    def login(self, username, password):
        try:
            self.jfs = jottalib.JFS.JFS(username, password)
            self.loginStatusChanged.emit(True)
        except Exception as e:
            print e
            self.loginStatusChanged.emit(False)

    def populateChildNodes(self, idx, oldidx):
        self.jottaModel.populateChildNodes(idx) # pass it on to model to expand children
        self.showJottaDetails(idx)

    def populateDevices(self):
        # devices = self.jfs.devices()
        self.ui.listDevices.addItems([d.name for d in self.jfs.devices])
        self.populateJottaRoot(unicode(self.ui.listDevices.currentText()))

    def populateJottaRoot(self, device):
        self.jottaModel = jottalib.qt.JFSModel(self.jfs, '/%s' % device)
        self.ui.jottafsView.setModel(self.jottaModel)
        self.ui.jottafsView.selectionModel().currentChanged.connect(self.populateChildNodes)

    def showJottaDetails(self, idx):
        # some item was single clicked/selected, show details
        item = self.jottaModel.itemFromIndex(idx)
        logging.debug('selected: %s' % unicode(item.text()))
        __details = self.ui.jottafsView.previewWidget()
        __details.findChild(QtGui.QLabel, 'details').setText("""
        <b>Name</b>: %s<br><b>Size:</b> %s<br><b>Created</b>: %s<br><b>Modified</b>:%s""" % \
                                                             (item.obj.name, item.obj.size,
                                                              item.obj.created, item.obj.modified))
        __preview = __details.findChild(QtGui.QLabel, 'thumbnail')
        __coverPix = QtGui.QPixmap()
        if isinstance(item, jottalib.qt.JFSFileNode) and item.obj.is_image():
            logging.debug('%s is an image, get thumb' % item.obj.name)
            __coverPix.loadFromData(item.obj.thumb(jottalib.JFS.JFSFile.MEDIUMTHUMB))
            # coverPix = coverPix.scaled(200,200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        __preview.setPixmap(__coverPix)

    def get(self):
        "Download current selected resource"
        dlfolder = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.PicturesLocation)
        selected = [self.jottaModel.itemFromIndex(idx) for idx in self.ui.jottafsView.selectedIndexes()]
        for item in selected:
            if isinstance(item, jottalib.qt.JFSFileNode):
                logging.debug('downloading %s ...' % item.obj.name)
                with open(os.path.join(dlfolder, '%s-jotta%s' % (item.obj.name, item.obj.revisionNumber), 'w+b') as f:
                    f.write(item.obj.read())
                    logging.info("Wrote %s", f.name)


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
