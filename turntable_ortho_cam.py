from    collections     import namedtuple
from    math            import sqrt, radians
from    PyQt5.QtCore    import QObject, pyqtSignal
import  glm

from    hardcoded_const import *

class TurntableOrthographicCamera( QObject ):

    def __init__( self ):
        super( TurntableOrthographicCamera, self ).__init__()

        # in radius
        self._azimuth                = 0 #type: float
        self._altitude               = 0 #type: float

    def GetViewMatrixOfTurntable( self, centerPivotPos: glm.vec3, height: float ) -> glm.mat4:
        return  glm.mat4().rotate( self._altitude, horizontalVec ) \
               *glm.mat4().rotate( self._azimuth, skyVec ) \
               *glm.mat4().translate( -centerPivotPos )

    def GetProjectionMatrixOfTurntable( self, radius: float, height: float )-> glm.mat4:
        fb = self.GetOriginFrameBoundary( radius, height )
        return glm.ortho( fb.left, fb.right, fb.bottom, fb.top, fb.near, fb.far )

    FrameBoundary = namedtuple( 'FrameBoundary', [ 'top', 'bottom', 'left', 'right', 'near', 'far' ] )

    @staticmethod
    def GetOriginFrameBoundary( radius: float, height: float )-> FrameBoundary:
        halfFrameHeight     = 0.5 *sqrt( height *height *0.25 + radius *radius ) *2.0

        return TurntableOrthographicCamera.FrameBoundary( halfFrameHeight, -halfFrameHeight,
                                                          -radius, radius,
                                                          halfFrameHeight, -halfFrameHeight )

    def GetLookVec( self )-> glm.vec3:
        return glm.inverse( self.GetViewMatrixOfTurntable() ) *lookVec

    def GetUpVec( self )-> glm.vec3:
        return glm.inverse( self.GetViewMatrixOfTurntable() ) *skyVec

    @property
    def azimuth( self ): return self._azimuth

    @property
    def altitude( self ): return self._altitude

    StateChanged = pyqtSignal()

    @azimuth.setter
    def azimuth( self, var: float ): self._azimuth = var; self.StateChanged.emit()

    @altitude.setter
    def altitude( self, var: float ): self._altitude = var; self.StateChanged.emit()

