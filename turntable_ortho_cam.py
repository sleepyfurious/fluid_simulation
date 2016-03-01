from    collections     import namedtuple
from    math            import sqrt, degrees
from    PyQt5.QtCore    import QObject, pyqtSignal
from    PyQt5.QtGui     import QMatrix4x4, QVector3D

from    hardcoded_const import *

class TurntableOrthographicCamera( QObject ):

    def __init__( self ):
        super( TurntableOrthographicCamera, self ).__init__()

        # in radius
        self._azimuth                = 0 #type: float
        self._altitude               = 0 #type: float

    def GetViewMatrixOfTurntable( self, centerPivotPos: QVector3D, height: float ) -> QMatrix4x4:
        # Qt's matrix transformation functionality is post-multiplication, and interpret angle in degrees
        ret = QMatrix4x4()
        ret.rotate( degrees( self._altitude ), horizontalVec )
        ret.rotate( degrees( self._azimuth ), skyVec )
        ret.translate( -centerPivotPos )
        return ret

    def GetProjectionMatrixOfTurntable( self, radius: float, height: float )-> QMatrix4x4:
        fb = self.GetOriginFrameBoundary( radius, height )
        ret = QMatrix4x4()
        ret.ortho( fb.left, fb.right, fb.bottom, fb.top, fb.near, fb.far )
        return ret

    # let say for camera near is start at >0 origin and far is a distance
    FrameBoundary = namedtuple( 'FrameBoundary', [ 'top', 'bottom', 'left', 'right', 'near', 'far' ] )

    @staticmethod
    def GetOriginFrameBoundary( radius: float, height: float )-> FrameBoundary:
        halfFrameHeight     = 0.5 *sqrt( height *height *0.25 + radius *radius ) *2.0

        return TurntableOrthographicCamera.FrameBoundary( halfFrameHeight, -halfFrameHeight,
                                                          -radius, radius,
                                                          -halfFrameHeight, halfFrameHeight )
    @property
    def azimuth( self ): return self._azimuth

    @property
    def altitude( self ): return self._altitude

    StateChanged = pyqtSignal()

    @azimuth.setter
    def azimuth( self, var: float ): self._azimuth = var; self.StateChanged.emit()

    @altitude.setter
    def altitude( self, var: float ): self._altitude = var; self.StateChanged.emit()