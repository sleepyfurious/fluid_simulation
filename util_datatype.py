from glm import mat4
from PyQt5.QtGui import QMatrix4x4

def GetGlmMat4( qMat: QMatrix4x4 ):
    return mat4( qMat.data() )