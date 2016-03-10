import  sys
from    PyQt5.QtCore    import QUrl, QPoint, QObject
from    PyQt5.QtGui     import QGuiApplication, QSurfaceFormat, QVector3D, QMatrix4x4
from    PyQt5.QtQuick   import QQuickView
from    OpenGL.GL       import *

from    looptimer           import  LoopTimer
import  qquickitem_glfbo    as      quickfbo
import  util_glwrapper      as      uglw
import  util_datatype       as      utyp
from    framerenderer       import  FrameRenderer
from    harris2004navierstroke    import  Harris2004NavierStrokeSimulation as H_GPU
from    direct_turntable_scenebox_ortho_cam import DirectManeuverTurntableSceneBoxOrthoCam

class FluidSimulationApp( quickfbo.GlFboViewportI ):
    def __init__(self):
        app = QGuiApplication( sys.argv )
        appView = QQuickView( QUrl.fromLocalFile("main.qml") )

        appViewOGLFormat = appView.format()  #type: QSurfaceFormat
        appViewOGLFormat.setProfile( QSurfaceFormat.CoreProfile )
        appViewOGLFormat.setVersion( 3, 3 )
        appView.setFormat( appViewOGLFormat )

        theAdapterInstance = appView.rootObject().findChild(
                                quickfbo.QquickItemFromGlFboViewportAdapter,
                                "glFboViewportAdapter"
                             )  #type: qquickitem_glfbo.QquickItemFromGlFboViewportAdapter
        theAdapterInstance.SetViewport( self )

        self.app                = app
        self.appView            = appView
        self.frameRenderer      = None
        self.loopTimer          = None
        self.frameCounter       = 0
        self.hgpu               = None
        self.sceneBoxSize       = QVector3D( 0.5, 0.5, 0.041 )
        self.sceneBoxCam        = DirectManeuverTurntableSceneBoxOrthoCam( self.sceneBoxSize )
        from math import radians
        # self.sceneBoxCam._cam.altitude=radians(90)

        self.qQuickWorkaround   = QMatrix4x4()
        self.qQuickWorkaround.scale( QVector3D( 1,-1, 1 ) )
        #- ^ this workaround QQuickFramebufferObject-QtQuick y-flip rendering bug

        self.last30DeltaTs = []

    def Exec ( self ):
        self.appView.show()
        # self.appView.setPosition(-1080,-1000) # this is for showing on current dev machine's second monitor
        self.app.exec()

    def Draw ( self, fboName: int, viewSize: QPoint ):
        # print( "frameCounter:", self.frameCounter )
        self.frameCounter += 1

        cellScale = 0.01
        gridSize    = tuple( int(x /cellScale) for x in utyp.GetTuple( self.sceneBoxSize ) )

        if not self.hgpu: self.hgpu = H_GPU( gridSize, cellScale )
        if not self.frameRenderer: self.frameRenderer = FrameRenderer( gridSize )
        if not self.loopTimer: self.loopTimer = LoopTimer()
        deltaT = self.loopTimer.GetElapsedInSecond()
        self.last30DeltaTs.append( deltaT );
        while len( self.last30DeltaTs ) > 30: self.last30DeltaTs.pop( 0 )

        glDisable( GL_BLEND )  # cleanup unexpected QQuick's GL state

        # realtime timestep simulation
        unitcellspaceBrushPositionXYZ = ( QVector3D(*gridSize ) *QVector3D( 0.1, 0.5, 0.5 ) ) -QVector3D(0.5,0.5,0.5)
        rUnitcellspaceHalfbrushSize = 2 /( 0.05 /cellScale )
        force = 100
        forceBrushLst = [ H_GPU.ForceBrush( rUnitcellspaceHalfbrushSize,
                                            unitcellspaceBrushPositionXYZ, QVector3D(force,0,0) ) ]
                          # H_GPU.ForceBrush( rUnitcellspaceHalfbrushSize,
                          #                   QVector3D(unitcellspaceBrushPositionXYZ.y(),
                          #                   unitcellspaceBrushPositionXYZ.x(),
                          #                   unitcellspaceBrushPositionXYZ.z()), QVector3D(0,force,0) )]
        self.hgpu.Step( deltaT, forceBrushLst )

        vpMat = self.qQuickWorkaround *self.sceneBoxCam.GetActiveVpMat()

        with uglw.FBOBound( fboName ):
            glClearBufferfv( GL_COLOR, 0, ( .2,.2,.2 ,1 ) )
            glViewport( 0, 0, viewSize.x(), viewSize.y() )
            with uglw.EnableScope( GL_BLEND ):
                glBlendFunc( GL_ONE, GL_ONE )

                self.frameRenderer.RenderToDrawBuffer_VelocityLine( vpMat,
                                                                    self.hgpu.GetTexnameOfCurrentVelocityField(),
                                                                    cellScale, 0.1 )
                self.frameRenderer.RenderToDrawBuffer_SceneBoxWire( vpMat, self.sceneBoxSize )

    def Cleanup ( self ):
        if self.frameRenderer:
            del self.framerenderer; self.frameRenderer = None
            del self.hgpu; self.hgpu = None

    def Synchronize( self ):
        root = self.appView.rootObject() #type: QObject

        if self.last30DeltaTs:
            sumDeltaTs = 0
            for dt in self.last30DeltaTs:
                sumDeltaTs += dt
            avgDeltaTs = sumDeltaTs /30
            root.setProperty( 'fpsDisplay', "%.2f"%(1 /avgDeltaTs) )

    def MousePressdMovedReleasedEvent ( self, e: quickfbo.MouseEvent, viewSize: QPoint ):
        activeVPMat = self.sceneBoxCam.GetActiveVpMat()
        lowerleftspaceMousePos = QPoint( e.pos.x(), viewSize.y() -e.pos.y() )

        if e.type == quickfbo.MouseEvent.PRESS:
            try: self.sceneBoxCam.StartManeuver( self.frameRenderer.GetSceneBoxCursorIntersection(
                    activeVPMat, self.sceneBoxSize, lowerleftspaceMousePos, viewSize ) )
            except ValueError: return

        if e.type == quickfbo.MouseEvent.MOVE:
            if not self.sceneBoxCam.IsManeuverStarted(): return

            self.sceneBoxCam.Maneuver(
                FrameRenderer.GetUnprojection( lowerleftspaceMousePos, 0., viewSize, activeVPMat ) )

        if e.type == quickfbo.MouseEvent.RELEASE:
            self.sceneBoxCam.FinishManeuver()


fluidSimulationApp = FluidSimulationApp()
fluidSimulationApp.Exec()
