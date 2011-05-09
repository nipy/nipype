import os

qt_api = os.environ.get('QT_API', 'pyqt')

if qt_api == 'pyqt':
    from PyQt4.QtOpenGL import *
else:
    from PySide.QtOpenGL import *

