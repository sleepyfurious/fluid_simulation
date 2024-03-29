from    collections     import namedtuple
from    math            import sqrt, degrees
from    PyQt5.QtGui     import QVector3D, QMatrix4x4

from    hardcoded_const import DirectionVec as dvec

class TurntableOrthographicCamera:

    def __init__( self, copyOriginal =None ):
        # in radius
        self.azimuth  = 0 #type: float
        self.altitude = 0 #type: float

        if not copyOriginal is None:
            self.azimuth  = copyOriginal.azimuth
            self.altitude = copyOriginal.altitude

    def GetViewMatrixOfTurntable( self, centerPivotPos: QVector3D, height: float ) -> QMatrix4x4:
        # Qt's matrix transformation method is post-multiplication, and interpret angle in degrees
        ret = QMatrix4x4()
        ret.rotate( degrees( self.altitude ), dvec.horizontalVec )
        ret.rotate( degrees( self.azimuth ), dvec.skyVec )
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