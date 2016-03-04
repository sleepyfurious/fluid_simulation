import  typing                  as T
from    PyQt5.QtGui             import QVector2D, QVector3D, QMatrix4x4
from    turntable_ortho_cam     import TurntableOrthographicCamera
from    manipulator_trackball   import ManipulatorTrackball
from    hardcoded_const         import DirectionVec as dvec

class DirectManeuverTurntableSceneBoxOrthoCam:

    def __init__( self, lSceneBoxSize: QVector3D ):
        self._cam               = TurntableOrthographicCamera()
        self._lSceneBoxSize     = lSceneBoxSize
        self._manipulatorBall   = None #type: ManipulatorTrackball

    def IsManeuverStarted( self )-> bool:
        return not self._manipulatorBall is None

    def GetActiveVpMat( self )-> QMatrix4x4:
        """:return: vpMat of Current Camera or inManeuvering Cam instead( in maneuvering )"""

        lSSize = self._lSceneBoxSize
        turntableRadius = QVector2D( lSSize.x() *0.5, lSSize.z() *0.5 ).length()

        activeCam = self._GetActiveCam()

        return activeCam.GetProjectionMatrixOfTurntable( turntableRadius, lSSize.y() ) \
               *activeCam.GetViewMatrixOfTurntable( QVector3D(), lSSize.y() )

    def StartManeuver( self, wPosCursorIntersection: QVector3D ):
        if self.IsManeuverStarted(): del self._manipulatorBall; self._manipulatorBall = None

        camLookVec, camUpVec = self._GetCamLookvecAndUpvec(
            self._GetActiveCam().GetViewMatrixOfTurntable( QVector3D(), self._lSceneBoxSize.y() ) )
        self._manipulatorBall = ManipulatorTrackball( QVector3D(), wPosCursorIntersection, camLookVec, camUpVec )

    def Maneuver( self, wPosCursorOrigin: QVector3D ):
        if not self.IsManeuverStarted(): raise AssertionError # false usage or internal implementation issue

        inMani_CamLookvec, inMani_CamUpvec = self._GetCamLookvecAndUpvec(
            self._GetActiveCam().GetViewMatrixOfTurntable( QVector3D(), self._lSceneBoxSize.y() ) )
        self._manipulatorBall.Manipulate( wPosCursorOrigin, inMani_CamLookvec, inMani_CamUpvec )

    def FinishManeuver( self ):
        if not self.IsManeuverStarted(): return
        if self._manipulatorBall.IsManipulated():
            self._ManipulatorBall_PushCam( self._cam )

        del self._manipulatorBall; self._manipulatorBall = None

    def CancelManeuver( self ):
        del self._manipulatorBall; self._manipulatorBall = None

    def _GetActiveCam( self ):
        ret = self._cam
        if self.IsManeuverStarted() and self._manipulatorBall.IsManipulated():
            inManipulatedCam = TurntableOrthographicCamera( self._cam )
            self._ManipulatorBall_PushCam( inManipulatedCam )
            ret = inManipulatedCam

        return ret

    def _ManipulatorBall_PushCam( self, targetCam: TurntableOrthographicCamera ):
        inManipulatedAngle = self._manipulatorBall.GetManipulatedAngle()
        targetCam.azimuth  += inManipulatedAngle.x()
        targetCam.altitude -= inManipulatedAngle.y()

    @staticmethod
    def _GetCamLookvecAndUpvec( viewMat: QMatrix4x4 )-> T.Tuple[ QVector3D, QVector3D ]:
        invertedVPMat, _ = viewMat.inverted()
        return invertedVPMat *dvec.lookVec, invertedVPMat *dvec.skyVec

