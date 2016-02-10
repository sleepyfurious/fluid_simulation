# An Interface class for making a OpenGL Viewport with QquickItemAdapter
#
# dev prerequisite in Qt 5.5.1 Reference Documentation:
# - Qt Quick > Scene Graph - OpenGL Under QML
# - Qt Quick > Scene Graph - Rendering FBOs

from    PyQt5.QtQml     import qmlRegisterType
from    PyQt5.QtQuick   import QQuickFramebufferObject
import  glm

"""Here is an Interface class for making a OpenGL Viewport"""
class GlFboViewportI:
    def __init__( self ):
        raise NotImplementedError

    def Cleanup( self ):
        raise NotImplementedError

    """ Implementation class draw into specified fbo using provided fboName. To let client consume the result fbo (e.g.
        show up on screen). Don't expect a clean OpenGL state. """
    def Draw( self, fboName: int, fboSize: glm.ivec2 ):
        raise NotImplementedError

class QquickItemFromGlFboViewportAdapter( QQuickFramebufferObject ):

    def __init__( self, parent=None ):
        super( QquickItemFromGlFboViewportAdapter, self ).__init__( parent )
        self.viewport = None #type: GlFboViewportI

    def SetViewport( self, viewport: GlFboViewportI ):
        self.viewport = viewport

    class _ViewportStub( QQuickFramebufferObject.Renderer ):
        def __init__( self, owner ):
            super( QquickItemFromGlFboViewportAdapter._ViewportStub, self ).__init__()
            self.owner = owner

        def synchronize( self, item ): pass

        def render( self ):
            if self.owner.viewport is None: return

            size = self.framebufferObject().size()
            self.owner.viewport.Draw( self.framebufferObject().handle(), glm.ivec2( size.width(), size.height() ) )
            self.owner.window().resetOpenGLState()

    #- below is to compile with QQuickFramebufferObject ----------------------------------------------------------------
    def createRenderer( self ) -> QQuickFramebufferObject.Renderer:
        return self._ViewportStub( self )

    def releaseResources( self ):
        if not self.viewport is None: self.viewport.Cleanup()
        super( QquickItemFromGlFboViewportAdapter, self ).releaseResources()

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