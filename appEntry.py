import  sys
from    PyQt5.QtCore    import QUrl
from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat
from    PyQt5.QtQuick   import QQuickView
import  glm

import  qquickitem_glfbo
import  framerenderer

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

    def Cleanup ( self ):
        if self.frameRenderer:
            del self.framerenderer
            self.frameRenderer = None


    def Draw ( self, fboName: int, fboSize: glm.ivec2 ):
        if not self.frameRenderer:
            self.frameRenderer = framerenderer.FrameRenderer()

        self.frameRenderer.RenderToDrawBuffer_VelocityLine( fboSize, glm.mat4() )

    def Exec ( self ):
        self.appView.show()
        self.app.exec()

fluidSimulationApp = FluidSimulationApp()
fluidSimulationApp.Exec()
