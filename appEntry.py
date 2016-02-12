import  sys
from    PyQt5.QtCore    import QUrl
from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat
from    PyQt5.QtQuick   import QQuickView
import  glm

import  qquickitem_glfbo
import  framerenderer
from    turntable_ortho_cam import *

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

        self.app        = app
        self.appView    = appView
        self.frameRenderer = None

        self.cam        = TurntableOrthographicCamera()

    def Exec ( self ):
        self.appView.show()
        self.app.exec()


    def Draw ( self, fboName: int, fboSize: glm.ivec2 ):
        self.cam.azimuth  += radians( 2 )
        self.cam.altitude += radians( 0.5 )

        if not self.frameRenderer:
            self.frameRenderer = framerenderer.FrameRenderer()

        sceneBoxHeight = 1.0
        vpMat =  self.cam.GetProjectionMatrixOfTurntable( 0.5, sceneBoxHeight ) \
                *self.cam.GetViewMatrixOfTurntable( glm.vec3( 0 ), sceneBoxHeight )

        self.frameRenderer.RenderToDrawBuffer_VelocityLine( fboSize, vpMat )

    def Cleanup ( self ):
        if self.frameRenderer:
            del self.framerenderer
            self.frameRenderer = None

fluidSimulationApp = FluidSimulationApp()
fluidSimulationApp.Exec()
