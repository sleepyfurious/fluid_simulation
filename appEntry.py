import  sys
from    math            import sqrt
from    PyQt5.QtCore    import QUrl
from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat
from    PyQt5.QtQuick   import QQuickView
import  glm

import  qquickitem_glfbo
import  framerenderer
from    turntable_ortho_cam import *
from    navierstroke import *
from    looptimer import *

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
        self.navierstrokeSim    = Harris2004NavierStrokeSimulation( ivec2(100), 0.2 )
        self.loopTimer          = None
        self.frameCounter       = 0

    def Exec ( self ):
        self.appView.show()
        self.app.exec()


    def Draw ( self, fboName: int, fboSize: glm.ivec2 ):
        print( "frameCounter:", self.frameCounter )
        self.frameCounter += 1

        self.cam.azimuth  += radians( 0.4 )
        self.cam.altitude += radians( 0.1 )

        if not self.frameRenderer:
            self.frameRenderer = framerenderer.FrameRenderer()

        if not self.loopTimer:
            self.loopTimer = LoopTimer()
        deltaT = self.loopTimer.GetElapsedInSecond()

        self.navierstrokeSim.Step( deltaT )

        sceneBoxSize = glm.vec3( 1.0, 1.0, 1.0 )
        sceneBoxTurntableRadius = sqrt( 0.25* sceneBoxSize.x *sceneBoxSize.x + 0.25 *sceneBoxSize.z *sceneBoxSize.z )
        vpMat =  self.cam.GetProjectionMatrixOfTurntable( sceneBoxTurntableRadius, sceneBoxSize.y ) \
                *self.cam.GetViewMatrixOfTurntable( glm.vec3( 0 ), sceneBoxSize.y )

        self.frameRenderer.RenderToDrawBuffer_VelocityLine(
            fboSize, vpMat, self.navierstrokeSim.GetACopyOfVelocity2DField2D() )

    def Cleanup ( self ):
        if self.frameRenderer:
            del self.framerenderer
            self.frameRenderer = None

fluidSimulationApp = FluidSimulationApp()
fluidSimulationApp.Exec()
