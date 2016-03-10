from PyQt5.QtGui import QMatrix4x4

def GetTuple( qtMathVector ):
    return qtMathVector.__reduce__()[1][2]