from    PyQt5.QtQuick import QQuickFramebufferObject
import  glm

class QquickGlFboItem( QQuickFramebufferObject ):
    """here is an Interface class for making a OpenGL Viewport. Client implements this Interface to use with
       QQuickGLFBOItem which is an adapter for this object for QtQuickItem """
    class ViewportI:

        def Cleanup( self ): pass

        """ client must draw into QtQuick's fbo using provided fboName. it's prebinded and glViewported """
        def Draw( self, fboName: int, fboSize: glm.ivec2 ): pass

    """ qmlRegisterType don't allow CTor assignment client must override this method to assign
       the implemented viewport """
    def AssignViewport( self ) -> ViewportI:
        return None

    def __init__( self, parent=None ):
        super( QquickGlFboItem, self ).__init__( parent )
        self.viewport = self.AssignViewport()

    class ViewportStub( QQuickFramebufferObject.Renderer ):
        def __init__( self, owner ):
            super( QquickGlFboItem.ViewportStub, self ).__init__( )
            self.owner = owner

        def synchronize( self, item ): pass

        def render( self ):
            size = self.framebufferObject().size()
            self.owner.viewport.Draw( self.framebufferObject().handle(), glm.ivec2( size.width(), size.height() ) )
            self.owner.window().resetOpenGLState()

    def createRenderer( self ) -> QQuickFramebufferObject.Renderer:
        return self.ViewportStub( self )

    def releaseResources( self ):
        self.viewport.Cleanup()
        super( QquickGlFboItem, self ).releaseResources( )


## USAGE EXAMPLE #######################################################################################################
if __name__ == "__main__":
    import  sys
    from    PyQt5.QtCore    import QUrl
    from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat
    from    PyQt5.QtQml     import qmlRegisterType
    from    PyQt5.QtQuick   import QQuickView
    from    OpenGL.GL       import *

    class HelloGLWorld( QquickGlFboItem.ViewportI ):

        def __init__(self):
            self.frameCount = 0
            self._qQuickGLFBOItem = QquickGlFboItem()

        def Cleanup ( self ): pass

        def Draw ( self, fboName: int, fboSize: glm.ivec2 ):

            if self.frameCount %100 > 50:
                glClearBufferfv( GL_COLOR, 0, ( 1, .5, .5, 1 ) )
            else:
                glClearBufferfv( GL_COLOR, 0, ( .5, 1, .5, 1 ) )

            self.frameCount = self.frameCount +1

        def GetQQuickItem( self ):
            return self._qQuickGLFBOItem

    app = QGuiApplication( sys.argv )

    class HelloGLWorldAdapter( QquickGlFboItem ):
        def AssignViewport ( self ):
            return HelloGLWorld()

    qmlRegisterType( HelloGLWorldAdapter, "HelloGLWorld", 1, 0, "HelloGLWorldItem" )

    view = QQuickView( QUrl.fromLocalFile("qquickitem_glfbo_sample.qml") )

    # edit opengl context version format
    oglFormat = view.format()
    oglFormat.setProfile(QSurfaceFormat.CoreProfile)
    oglFormat.setVersion(3,3)
    view.setFormat(oglFormat)

    view.show()

    sys.exit( app.exec() )