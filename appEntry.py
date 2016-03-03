import  sys
from    PyQt5.QtCore    import QUrl, Qt, QPoint
from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat
from    PyQt5.QtQuick   import QQuickView
from    OpenGL.GL       import *
import  glm

import  qquickitem_glfbo
import  framerenderer
from    turntable_ortho_cam import *
from    navierstroke import *
from    looptimer import *
import  util_datatype as utyp
import util_glwrapper as uglw

class FluidSimulationApp( qquickitem_glfbo.GlFboViewportI ):
    def __init__(self):
        app = QGuiApplication( sys.argv )
        appView = QQuickView( QUrl.fromLocalFile("main.qml") )

        appViewOGLFormat = appView.format()  #type: QSurfaceFormat
        appViewOGLFormat.setProfile( QSurfaceFormat.CoreProfile )
        appViewOGLFormat.setVersion( 3, 3 )
        appView.setFormat( appViewOGLFormat )

        theAdapterInstance = appView.rootObject().findChild(
                                qquickitem_glfbo.QquickItemFromGlFboViewportAdapter,
                                "glFboViewportAdapter"
                             )  #type: qquickitem_glfbo.QquickItemFromGlFboViewportAdapter
        theAdapterInstance.SetViewport( self )

        self.app                = app
        self.appView            = appView
        self.frameRenderer      = None
        self.cam                = TurntableOrthographicCamera()
        self.navierstrokeSim    = Harris2004NavierStrokeSimulation( ivec2(10), 1.0 )
        self.sceneBoxSize       = QVector3D( 10, 10, 1 )
        self.loopTimer          = None
        self.frameCounter       = 0

    def Exec ( self ):
        self.appView.show()
        self.app.exec()


    def Draw ( self, fboName: int, fboSize: glm.ivec2 ):
        print( "frameCounter:", self.frameCounter )
        self.frameCounter += 1

        if not self.frameRenderer:
            self.frameRenderer = framerenderer.FrameRenderer( tuple( self.navierstrokeSim.gridSize ) +( 1,) )

        if not self.loopTimer:
            self.loopTimer = LoopTimer()
        deltaT = self.loopTimer.GetElapsedInSecond()

        # # fixed timestep simulation
        # self.navierstrokeSim.Step( 0.04 )
        # realtime timestep simulation
        self.navierstrokeSim.Step( deltaT )

        vpMat = self._GetVPMat()

        with uglw.FBOBound( fboName ):
            glClearBufferfv( GL_COLOR, 0, ( .2,.2,.2 ,1 ) )
            with uglw.EnableScope( GL_BLEND ):
                glBlendFunc( GL_ONE, GL_ONE )

                self.frameRenderer.RenderToDrawBuffer_VelocityLine( vpMat,
                                                                    self.navierstrokeSim.GetACopyOfVelocity2DField2D(),
                                                                    self.navierstrokeSim.gridSpacing )
                self.frameRenderer.RenderToDrawBuffer_SceneBoxWire( vpMat, self.sceneBoxSize )

    def Cleanup ( self ):
        if self.frameRenderer:
            del self.framerenderer
            self.frameRenderer = None

    def MousePressdMovedReleasedEvent ( self, e: qquickitem_glfbo.MouseEvent, viewSize: QPoint ):
        if e.type == qquickitem_glfbo.MouseEvent.PRESS:
            wPosCursorIntersection = self.frameRenderer.GetSceneBoxCursorIntersection(
                                        self._GetVPMat(), self.sceneBoxSize,
                                        QPoint( e.pos.x(), viewSize.y() -e.pos.y() ), viewSize
                                     )


    def _GetVPMat( self )-> QMatrix4x4:
        # camera matrix
        sceneBoxSize = utyp.GetTuple( self.sceneBoxSize )
        sceneBoxTurntableRadius = sqrt( 0.25 *sceneBoxSize[0] *sceneBoxSize[0] +0.25 *sceneBoxSize[2] *sceneBoxSize[2] )
        ret =  self.cam.GetProjectionMatrixOfTurntable( sceneBoxTurntableRadius, sceneBoxSize[1] ) \
               *self.cam.GetViewMatrixOfTurntable( QVector3D(), sceneBoxSize[1] )

        qQuickWorkaround = QMatrix4x4()
        qQuickWorkaround.scale( QVector3D( 1,-1, 1 ) )
        #- ^ this workaround QQuickFramebufferObject-QtQuick y-flip rendering bug

        return qQuickWorkaround *ret


fluidSimulationApp = FluidSimulationApp()
fluidSimulationApp.Exec()
