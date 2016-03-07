"As noted"

import  typing          as T
from    PyQt5.QtCore    import QPoint
from    PyQt5.QtGui     import QVector2D, QVector3D, QVector4D, QMatrix4x4
from    OpenGL.GL       import *

import  util_datatype   as utyp
import  util_glwrapper  as uglw
from    util_glshaderwrangler           import BuildPipelineProgram
import  framerenderer_glsw              as glsw
from    sleepy_mockup_glslsampler       import Vec2DField2D
from    framerenderer_offscreendepth    import OffScreenDepthFramebuffer


"""All method must be invoked in the same living OpenGL 3.3 context"""
class FrameRenderer:
    def __init__( self, fieldSize: T.Tuple[ int, int, int ] ):
        self._fieldSize = fieldSize
        self._vao_blank = glGenVertexArrays( 1 )
        self._velocityLineProgramInfo = BuildPipelineProgram( glsw.v, glsw.f, ( "GRID",) )
        self._sceneBoxWireProgramInfo = BuildPipelineProgram( glsw.v, glsw.f, ( "SCENEBOX", "LINE" ) )
        self._sceneBoxSurfProgramInfo = BuildPipelineProgram( glsw.v, glsw.f, ( "SCENEBOX", "SURF" ) )
        self._depthInteractionBuffer  = OffScreenDepthFramebuffer()

        with uglw.ProgBound( self._velocityLineProgramInfo.__progHandle__ ):
            glUniform3iv( self._velocityLineProgramInfo.gridN, 1, fieldSize )

    def __del__(self):
        glDeleteVertexArrays( [ self._vao_blank ] )
        glDeleteProgram( self._velocityLineProgramInfo.__progHandle__ )
        glDeleteProgram( self._sceneBoxWireProgramInfo.__progHandle__ )
        glDeleteProgram( self._sceneBoxSurfProgramInfo.__progHandle__ )
        del self._depthInteractionBuffer

    def RenderToDrawBuffer_VelocityLine ( self, vpMat: QMatrix4x4,
        texName_velocityField3D: GLuint, fieldSpacing: float
    ):
        with uglw.VAOBound( self._vao_blank ):
            with uglw.TextureBound( GL_TEXTURE_3D, texName_velocityField3D ):
                with uglw.ProgBound( self._velocityLineProgramInfo.__progHandle__ ):
                    cellNx2 = self._fieldSize[0] *self._fieldSize[1] *self._fieldSize[2] *2

                    glUniform1fv( self._velocityLineProgramInfo.gridSpacing, 1, fieldSpacing )
                    glUniformMatrix4fv( self._velocityLineProgramInfo.vpMat, 1, GL_FALSE, vpMat.data() )
                    glDrawArrays( GL_LINES, 0, cellNx2 )
                    glDrawArrays( GL_POINTS, 0, cellNx2 )

    def RenderToDrawBuffer_SceneBoxWire ( self, vpMat: QMatrix4x4, boxSize: QVector3D ):
        with uglw.VAOBound( self._vao_blank ):
            with uglw.ProgBound( self._sceneBoxWireProgramInfo.__progHandle__ ):
                glUniform3fv( self._sceneBoxWireProgramInfo.boxSize, 1, utyp.GetTuple( boxSize ) )
                glUniformMatrix4fv( self._sceneBoxWireProgramInfo.vpMat, 1, GL_FALSE, vpMat.data() )
                glDrawArrays( GL_LINES, 0, 24 )

    def GetSceneBoxCursorIntersection (
        self, vpMat: QMatrix4x4, boxSize: QVector3D, winspaceCursorPos: QPoint, winspaceDimension: QPoint
    )-> QVector3D:
        """
        :param winspaceCursorPos: lower-left corner as origin
        :return: 3D world position of cursor interaction
        """

        # render depthImage and get depthValue -------------------------------------------------------------------------
        self._depthInteractionBuffer.RequestBindFBO( winspaceDimension )

        with uglw.VAOBound( self._vao_blank ):
            with uglw.ProgBound( self._sceneBoxSurfProgramInfo.__progHandle__ ):
                with uglw.EnableScope( GL_DEPTH_TEST ):
                    glClearBufferfv( GL_DEPTH, 0, ( 1., ) )
                    glUniform3fv( self._sceneBoxSurfProgramInfo.boxSize, 1, utyp.GetTuple( boxSize ) )
                    glUniformMatrix4fv( self._sceneBoxSurfProgramInfo.vpMat, 1, GL_FALSE, vpMat.data() )
                    glDrawArrays( GL_TRIANGLES, 0, 3 *2 *6 )

        winspaceCursorDepthValue = glReadPixels( winspaceCursorPos.x(), winspaceCursorPos.y(), 1, 1,
                                                 GL_DEPTH_COMPONENT, GL_FLOAT )[0][0]
        # print( winspaceCursorDepthValue )

        glBindFramebuffer( GL_FRAMEBUFFER, 0 )

        # unproject cursor into worldCoord -----------------------------------------------------------------------------
        if winspaceCursorDepthValue == 1.0:
            raise ValueError # cursor ray hit background, no object to manipulate

        return self.GetUnprojection( winspaceCursorPos, winspaceCursorDepthValue, winspaceDimension, vpMat )

    @staticmethod
    def GetUnprojection( winXY: QPoint, winZ: float, winWH: QPoint, vpMat: QMatrix4x4 )-> QVector3D:
        #- from gluUnproject definition, I don't consider glViewport
        ndcspaceCursorPos = QVector4D( ( QVector2D(winXY) /QVector2D(winWH) ) *2 -QVector2D(1,1), winZ *2 -1, 1 )

        invertedVpMat, success = vpMat.inverted()
        if not success: raise NotImplementedError
        wspaceCursorPos = invertedVpMat *ndcspaceCursorPos

        return QVector3D( wspaceCursorPos ) /wspaceCursorPos.w()