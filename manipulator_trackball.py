from math import sqrt
from collections import namedtuple
from glm import *

def _Length( v: vec3 ):
    sqrtLength = 0
    for element in list( v ):
        sqrtLength += element *element
    return sqrt( sqrtLength )

def _GetPointOnSphere( centerPos: vec3, radius: float, surfaceNormal: vec3 ):
    """surfaceNormal: assumed normalized"""
    return centerPos + radius *surfaceNormal

def _Dot( a: vec3, b: vec3 ):
    return a.x *b.x + a.y *b.y + a.z *b.z

_floatEpsilon = 7./3 - 4./3 -1 # see: http://stackoverflow.com/questions/19141432/python-numpy-machine-epsilon

def _Cross( a: vec3, b: vec3 ):
    return vec3( a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x )

_Sphere = namedtuple( 'Sphere', [ 'centerPos', 'radius' ] )
_Plain = namedtuple( 'Plain', [ 'samplePos', 'normal' ] )

class ManipulatorTrackball:
    """As Noted"""

    def __init__( self,
        sphereCenterPos: vec3, startCursorPos: vec3, camLookVec: vec3, camUpVec: vec3
    ):
        """vecs assumed normalized"""

        self._interactionTrackballRadius = _Length( startCursorPos - sphereCenterPos )

        self._interactionSphere = _Sphere( sphereCenterPos, self._interactionTrackballRadius )

        interactionPlain = self.GetTangentingPlainOfSphere( self._interactionSphere.centerPos,
                                                            self._interactionTrackballRadius, -camLookVec  )

        self._startPosInInteractionPlain =  self.GetInteractionPosInInteractionPlain(
                                                startCursorPos, camLookVec, interactionPlain, camLookVec, camUpVec )

    def GetManipulationVec( self, cursorOrigin: vec3, camLookVec: vec3, camUpVec: vec3 )-> vec2:
        """:return: interaction's diffVector"""
        interactionPlain = self.GetTangentingPlainOfSphere( self._interactionSphere.centerPos,
                                                            self._interactionTrackballRadius, -camLookVec  )
        endPosInInteractionPlain =  self.GetInteractionPosInInteractionPlain(
                                        cursorOrigin, camLookVec, interactionPlain, camLookVec, camUpVec )

        return endPosInInteractionPlain -self._startPosInInteractionPlain

    @staticmethod
    def GetTangentingPlainOfSphere( sphCenterPos: vec3, sphRadius: float, sphereNormal: vec3 )-> _Plain:
        """Get a tangenting plain of a sphere with the tangent being the plain's sampled point."""
        return _Plain( _GetPointOnSphere( sphCenterPos, sphRadius, sphereNormal ),
                                          sphereNormal )
    @staticmethod
    def GetInteractionPosInInteractionPlain(
        cursorRaySampledPosition: vec3, cursorVec: vec3, interactionPlain: _Plain, camLookVec: vec3, camUpVec: vec3
    ):
        """vecs assumed normalized"""

        # trace our cursor Pos back to the interaction plain
        sampledPointOfInteractionRay = cursorRaySampledPosition -cursorVec
        if _Dot( cursorRaySampledPosition -sampledPointOfInteractionRay, interactionPlain.normal ) <= _floatEpsilon :
            raise ValueError # undefinded interaction

        # from cyrusbeck.pdf (Cyrus Beck Line Clipping) in workspace 20131221.CUCG.projectRat
        _untitled = _Dot( cursorRaySampledPosition -interactionPlain.samplePos, interactionPlain.normal )
        _t = _untitled /(
                _untitled -_Dot( sampledPointOfInteractionRay -interactionPlain.samplePos, interactionPlain.normal )
        )
        interactionplainCursorRayIntersectionPoint = cursorRaySampledPosition -cursorVec *_t
        interactionplainCursorRayIntersectionVec = interactionplainCursorRayIntersectionPoint \
                                                 - interactionPlain.samplePos
        camRightVec = _Cross( camLookVec, camUpVec )

        return vec2( _Dot( camRightVec, interactionplainCursorRayIntersectionVec ),
                     _Dot( camUpVec, interactionplainCursorRayIntersectionVec ) )

