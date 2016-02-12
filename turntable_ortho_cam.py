from collections import namedtuple
from math import *
import glm

from hardcoded_const import *

class TurntableOrthographicCamera:

    def __init__( self ):
        self.azimuth                = 0 # |- in radius
        self.altitude               = 0 # |

    FrameBoundary = namedtuple( 'FrameBoundary', [ 'top', 'bottom', 'left', 'right', 'near', 'far' ] )

    def GetViewMatrixOfTurntable( self ) -> glm.mat4:
        return glm.rotate( glm.mat4(), -self.altitude, horVec ) *glm.rotate( glm.mat4(), self.azimuth , skyVec )

    def GetProjectionMatrixOfTurntable( self, bottomCenterPos: glm.vec3, radius: float, height: float )-> glm.mat4:
        fb = self.GetOriginFrameBoundary( bottomCenterPos, radius, height )
        return glm.ortho( fb.left, fb.right, fb.bottom, fb.top, fb.near, fb.far )

    @staticmethod
    def GetOriginFrameBoundary( bottomCenterPos: glm.vec3, radius: float, height: float )-> FrameBoundary:
        frameHeight     = sqrt( height *height *0.25 + radius *radius ) *2.0
        frameWidth      = radius
        halfFrameDepth  = 0.5 *frameHeight

        heightElevationMaxMargin = 0.5 *( frameHeight -height )

        return TurntableOrthographicCamera.FrameBoundary( frameHeight +heightElevationMaxMargin,
                                                          -heightElevationMaxMargin,
                                                          -radius, radius,
                                                          halfFrameDepth, -halfFrameDepth )

    def GetLookVec( self )-> glm.vec3:
        return glm.inverse( self.GetViewMatrixOfTurntable() ) *lookVec

    def GetUpVec( self )-> glm.vec3:
        return glm.inverse( self.GetViewMatrixOfTurntable() ) *skyVec