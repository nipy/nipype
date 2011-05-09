import os

qt_api = os.environ.get('QT_API', 'pyqt')

if qt_api == 'pyqt':
    from PyQt4.QtWebKit import *
else:
    from PySide.QtWebKit import *

