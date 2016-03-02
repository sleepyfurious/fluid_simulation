from glm import mat4
from PyQt5.QtGui import QMatrix4x4

def GetGlmMat4( qMat: QMatrix4x4 ):
    return mat4( qMat.data() )

def GetTuple( qtMathVector ):
    return qtMathVector.__reduce__()[1][2]