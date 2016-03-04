from collections import namedtuple
from PyQt5.QtGui import QVector2D, QVector3D

def _GetPointOnSphere( centerPos: QVector3D, radius: float, surfaceNormal: QVector3D )-> QVector3D:
    """surfaceNormal: assumed normalized"""
    return centerPos +radius *surfaceNormal

_floatEpsilon = 7./3 - 4./3 -1 # see: http://stackoverflow.com/questions/19141432/python-numpy-machine-epsilon

_Sphere = namedtuple( 'Sphere', [ 'centerPos', 'radius' ] )
_Plain = namedtuple( 'Plain', [ 'samplePos', 'normal' ] )

class ManipulatorTrackball:
    """As Noted"""

    def __init__( self,
        sphereCenterPos: QVector3D, startCursorPos: QVector3D, camLookVec: QVector3D, camUpVec: QVector3D
    ):
        """input vecs assumed normalized"""
        self._interactionVectorOnInteractionPlain = None #type: QVector2D

        self._interactionTrackballRadius = ( startCursorPos -sphereCenterPos ).length()
        self._interactionSphere = _Sphere( sphereCenterPos, self._interactionTrackballRadius )
        interactionPlain = self.GetTangentingPlainOfSphere( self._interactionSphere.centerPos,
                                                            self._interactionTrackballRadius, -camLookVec  )

        self._startPosOnInteractionPlain =  self.GetInteractionPosInInteractionPlain(
                                                startCursorPos, camLookVec, interactionPlain, camLookVec, camUpVec )

    def Manipulate( self, cursorOrigin: QVector3D, camLookVec: QVector3D, camUpVec: QVector3D ):
        interactionPlain = self.GetTangentingPlainOfSphere( self._interactionSphere.centerPos,
                                                            self._interactionTrackballRadius, -camLookVec  )
        endPosOnInteractionPlain =  self.GetInteractionPosInInteractionPlain(
                                        cursorOrigin, camLookVec, interactionPlain, camLookVec, camUpVec )

        self._interactionVectorOnInteractionPlain = endPosOnInteractionPlain -self._startPosOnInteractionPlain

    def IsManipulated(self)-> bool:
        return not self._interactionVectorOnInteractionPlain is None

    def GetManipulatedAngle( self )-> QVector2D:
        if self._interactionVectorOnInteractionPlain is None: raise AssertionError # false usage or internal class error
        return self._interactionVectorOnInteractionPlain /self._interactionTrackballRadius

    @staticmethod
    def GetTangentingPlainOfSphere( sphCenterPos: QVector3D, sphRadius: float, tangentingNormal: QVector3D )-> _Plain:
        """Get a tangenting plain of a sphere with the tangent being the plain's sampled point."""
        return _Plain( _GetPointOnSphere( sphCenterPos, sphRadius, tangentingNormal ),
                                          tangentingNormal )
    @staticmethod
    def GetInteractionPosInInteractionPlain( cursorRaySampledPosition: QVector3D, cursorVec: QVector3D,
                                             interactionPlain: _Plain, camLookVec: QVector3D, camUpVec: QVector3D ):
        """vecs assumed normalized"""

        # trace our cursor Pos back to the interaction plain
        sampledPointOfInteractionRay = cursorRaySampledPosition -cursorVec
        if QVector3D.dotProduct( sampledPointOfInteractionRay -cursorRaySampledPosition, interactionPlain.normal ) \
           <= _floatEpsilon :
            raise ValueError # undefinded interaction

        # from cyrusbeck.pdf (Cyrus Beck Line Clipping) in workspace 20131221.CUCG.projectRat
        _untitled = QVector3D.dotProduct( cursorRaySampledPosition -interactionPlain.samplePos,
                                          interactionPlain.normal )
        _t = _untitled /( _untitled -
                          QVector3D.dotProduct( sampledPointOfInteractionRay -interactionPlain.samplePos,
                                                interactionPlain.normal ) )

        interactionplainCursorRayIntersectionPoint = cursorRaySampledPosition -cursorVec *_t
        interactionplainCursorRayIntersectionVec = interactionplainCursorRayIntersectionPoint \
                                                 - interactionPlain.samplePos
        camRightVec = QVector3D.crossProduct( camLookVec, camUpVec )

        return QVector2D( QVector3D.dotProduct( camRightVec, interactionplainCursorRayIntersectionVec ),
                          QVector3D.dotProduct( camUpVec, interactionplainCursorRayIntersectionVec ) )

