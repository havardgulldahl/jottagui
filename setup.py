# -*- encoding: utf-8 -*-
"""
Create OSX app

Usage:
    python setup.py py2app
"""


import sys, os.path
from setuptools import setup

if sys.platform == 'win32':
	import py2exe

def getversion():
    if sys.platform == 'darwin':
        _p = 'MAC'
    elif sys.platform == 'win32':
        _p = 'WIN'
    else:
        _p = 'x'

mainscript = os.path.join('src', 'main.py')

INCLUDES=['sip', 'PyQt4.QtCore', 'PyQt4.QtGui', 'lxml.objectify', 'lxml.etree', 'lxml._elementpath']
EXCLUDES=['PyQt4.QtDesigner', 'PyQt4.QtNetwork', 'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtSql',
          'PyQt4.QtTest', 'PyQt4.QtWebKit', 'PyQt4.QtXml', 'PyQt4.phonon']

if sys.platform == 'darwin':
     extra_options = dict(
         setup_requires=['py2app'],
         app=[mainscript],
         # Cross-platform applications generally expect sys.argv to
         # be used for opening files.
         options=dict(py2app=dict(
             argv_emulation=True,
             #iconfile='jottagui.icns',
             #packages=['lxml'],
             includes=INCLUDES,
             excludes=EXCLUDES,
             frameworks=['/usr/lib/libxml2.2.dylib',],
             resources=['src/cacert.pem',],
             plist=dict(CFBundleIdentifier='no.lurtgjort.apps.jottagui',
                        CFBundleShortVersionString='JottaGui, version 0.1',
                        NSSupportsSuddenTermination=False,
                        NSHumanReadableCopyright='havard@gulldahl.no 2012-2014')
             )
         ),
     )
elif sys.platform == 'win32':
     extra_options = dict(
         setup_requires=['py2exe'],
         windows=[mainscript],
		     packages=['gui','metadata',],
		     package_dir={},
		     options=dict(py2exe=dict(
             #packages=['lxml'],
             includes=INCLUDES,
             excludes=EXCLUDES,
		         )
         )
      )
else:
     extra_options = dict(
         # Normally unix-like platforms will use "setup.py install"
         # and install the main script as such
         scripts=[mainscript],
     )

setup(
    name="JottaGui",
    version="0.1",
    author=u'Håvard Gulldahl',
    author_email='havard@gulldahl.no',
    description='A simple JottaCloud client (unofficial)',

    **extra_options
)
