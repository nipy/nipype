import os

qt_api = os.environ.get('QT_API', 'pyqt')

if qt_api == 'pyqt':
    from PyQt4.QtSvg import *
else:
    from PySide.QtSvg import *

