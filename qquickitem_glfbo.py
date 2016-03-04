# An Interface class for making a OpenGL Viewport with QquickItemFromGlFboViewportAdapter
#
# dev prerequisite in Qt 5.5.1 Reference Documentation:
# - Qt Quick > Scene Graph - OpenGL Under QML
# - Qt Quick > Scene Graph - Rendering FBOs
# - Qt Quick > Scene Graph - Qt Quick Scene Graph > Scene Graph and Rendering ( Threading )

from    PyQt5.QtCore    import Qt, QPoint
from    PyQt5.QtQml     import qmlRegisterType
from    PyQt5.QtQuick   import QQuickFramebufferObject
from    PyQt5.QtGui     import QMouseEvent

import  util_datatype   as utyp

class MouseEvent:
    PRESS   = 1
    RELEASE = 2
    MOVE    = 3
    _eventName = { 1:"press", 2:"release", 3:"move" }

    def __init__( self, type, pos: QPoint ):
        self.type  = type
        self.pos   = pos

    def __str__(self):
        return "MouseEvent: " +self._eventName[ self.type ] + " @" +str(self.pos.x()) +',' +str(self.pos.y())

# an Interface class for making a OpenGL Viewport
class GlFboViewportI:
    def __init__( self ): raise NotImplementedError

    # To let client consume the result fbo (e.g. show up on screen). Implementation class draw into specified fbo using
    # provided fboName. GLContext will pre-makeCurrented, don’t expect a clean OpenGL state, also check/create GLContext
    # dependent here.
    def Draw( self, fboName: int, viewSize: QPoint ): raise NotImplementedError

    # Cleanup everything GLContext dependent here.
    def Cleanup( self ): raise NotImplementedError

    def MousePressdMovedReleasedEvent( self, e: MouseEvent, viewSize: QPoint ): raise NotImplementedError

class QquickItemFromGlFboViewportAdapter( QQuickFramebufferObject ):

    def __init__( self, parent=None ):
        super( QquickItemFromGlFboViewportAdapter, self ).__init__( parent )
        self._viewport = None #type: GlFboViewportI
        self._eventQueue = []
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

            size = QPoint( *utyp.GetTuple( self.framebufferObject().size() ) )

            for e in self.owner._eventQueue:
                self.owner._viewport.MousePressdMovedReleasedEvent( e, size )
            self.owner._eventQueue = []

            self.owner._viewport.Draw( self.framebufferObject().handle(), size )
            self.owner.window().resetOpenGLState()

    #- below is to compile with QQuickFramebufferObject ----------------------------------------------------------------
    def createRenderer( self ) -> QQuickFramebufferObject.Renderer:
        return self._ViewportStub( self )

    def releaseResources( self ):
        if not self._viewport is None: self._viewport.Cleanup( )
        super( QquickItemFromGlFboViewportAdapter, self ).releaseResources()

    #- below is input event redirection
    def mouseReleaseEvent ( self, e: QMouseEvent ): self.QueueMouseEvent( e )
    def mousePressEvent ( self, e: QMouseEvent ):   self.QueueMouseEvent( e )
    def mouseMoveEvent ( self, e: QMouseEvent ):    self.QueueMouseEvent( e )
    def QueueMouseEvent ( self, e: QMouseEvent ):
        # Queue so that GlFboViewport can process it in RenderingThread. consumer and provider have no overlapping
        # execution between GUI and Rendering Thread, so that we can assume thread-safety. I queue our own MouseEvent
        # class so that it's data is not interfere by Qt's GUI thread, i.e. delete event before rendering
        if self._viewport is None: return

        if e.button() == Qt.LeftButton:
            if      e.type() == QMouseEvent.MouseButtonPress:
                self._eventQueue.append( MouseEvent( MouseEvent.PRESS, e.pos() ) )
            elif    e.type() == QMouseEvent.MouseButtonRelease:
                self._eventQueue.append( MouseEvent( MouseEvent.RELEASE, e.pos() ) )

        elif e.type() == QMouseEvent.MouseMove:
            self._eventQueue.append( MouseEvent( MouseEvent.MOVE, e.pos() ) )


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

        def Draw ( self, fboName: int, viewSize: QPoint):
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