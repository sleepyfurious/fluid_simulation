# An Interface class for making a OpenGL Viewport with QquickItemFromGlFboViewportAdapter
#
# dev prerequisite in Qt 5.5.1 Reference Documentation:
# - Qt Quick > Scene Graph - OpenGL Under QML
# - Qt Quick > Scene Graph - Rendering FBOs

from    PyQt5.QtCore    import Qt
from    PyQt5.QtQml     import qmlRegisterType
from    PyQt5.QtQuick   import QQuickFramebufferObject
from    PyQt5.QtGui     import QMouseEvent
import  glm

# an Interface class for making a OpenGL Viewport
class GlFboViewportI:
    def __init__( self ): raise NotImplementedError

    # To let client consume the result fbo (e.g. show up on screen). Implementation class draw into specified fbo using
    # provided fboName. GLContext will pre-makeCurrented, don’t expect a clean OpenGL state, also check/create GLContext
    # dependent here.
    def Draw( self, fboName: int, fboSize: glm.ivec2 ): raise NotImplementedError

    # Cleanup everything GLContext dependent here.
    def Cleanup( self ): raise NotImplementedError

    def MousePressdMovedReleasedEvent( self, e: QMouseEvent ): raise NotImplementedError

class QquickItemFromGlFboViewportAdapter( QQuickFramebufferObject ):

    def __init__( self, parent=None ):
        super( QquickItemFromGlFboViewportAdapter, self ).__init__( parent )
        self._viewport = None #type: GlFboViewportI
        self.setAcceptedMouseButtons( Qt.AllButtons )

    def SetViewport( self, viewport: GlFboViewportI ):
        self._viewport = viewport

    class _ViewportStub( QQuickFramebufferObject.Renderer ):
        def __init__( self, owner ):
            super( QquickItemFromGlFboViewportAdapter._ViewportStub, self ).__init__()
            self.owner = owner

        def synchronize( self, item ): pass

        def render( self ):
            if self.owner._viewport is None: return

            size = self.framebufferObject().size()
            self.owner._viewport.Draw( self.framebufferObject().handle(), glm.ivec2( size.width(), size.height() ) )
            self.owner.window().resetOpenGLState()

    #- below is to compile with QQuickFramebufferObject ----------------------------------------------------------------
    def createRenderer( self ) -> QQuickFramebufferObject.Renderer:
        return self._ViewportStub( self )

    def releaseResources( self ):
        if not self._viewport is None: self._viewport.Cleanup( )
        super( QquickItemFromGlFboViewportAdapter, self ).releaseResources()

    #- below is input event redirection
    def mouseReleaseEvent ( self, e: QMouseEvent ):
        if not self._viewport is None: self._viewport.MousePressdMovedReleasedEvent( e )
    def mousePressEvent ( self, e: QMouseEvent ):
        if not self._viewport is None: self._viewport.MousePressdMovedReleasedEvent( e )
    def mouseMoveEvent ( self, e: QMouseEvent ):
        if not self._viewport is None: self._viewport.MousePressdMovedReleasedEvent( e )

qmlRegisterType( QquickItemFromGlFboViewportAdapter, "GlFboViewport", 1, 0, "GlFboViewportAdapter" )

## USAGE EXAMPLE #######################################################################################################
if __name__ == "__main__":
    import  sys
    from    PyQt5.QtCore    import QUrl
    from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat
    from    PyQt5.QtQuick   import QQuickView
    from    OpenGL.GL       import *

    # create an app, create a window with sample qml
    app = QGuiApplication( sys.argv )
    view = QQuickView( QUrl.fromLocalFile("qquickitem_glfbo_sample.qml") )

    # specify OpenGL context version
    oglFormat = view.format()
    oglFormat.setProfile(QSurfaceFormat.CoreProfile)
    oglFormat.setVersion(3,3)
    view.setFormat(oglFormat)

    # define our viewport
    class HelloGLWorld( GlFboViewportI ):

        def __init__(self):
            self.frameCount = 0

        def Cleanup ( self ): pass

        def Draw ( self, fboName: int, fboSize: glm.ivec2 ):
            if self.frameCount %100 > 50:
                glClearBufferfv( GL_COLOR, 0, ( 1, .5, .5, 1 ) )
            else:
                glClearBufferfv( GL_COLOR, 0, ( .5, 1, .5, 1 ) )

            self.frameCount = self.frameCount +1

    ourGlViewport = HelloGLWorld()

    # set our viewport into the loaded qml,
    # see: Qt 5.5.1 Reference Documentation > Qt QML > Interacting with QML Objects from C++
    theAdapterInstance = view.rootObject().findChild(
                            QquickItemFromGlFboViewportAdapter,
                            "helloOurViewportAdapter") #type: QquickItemFromGlFboViewportAdapter
    theAdapterInstance.SetViewport( ourGlViewport )

    # let the result shown
    view.show()
    sys.exit( app.exec() )