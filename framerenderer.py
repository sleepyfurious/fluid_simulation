"As noted"

from PyQt5.QtCore import QPoint
from PyQt5.QtGui  import QMatrix4x4, QVector3D
from OpenGL.GL import *
import glm

import util_datatype    as utyp
import util_glwrapper as uglw
from sleepy_mockup_glslsampler import *
from util_glshaderwrangler import BuildPipelineProgram
import framerenderer_glsw as glsw
from framerenderer_offscreendepth import *


"""All method must be invoked in the same living OpenGL 3.3 context"""
class FrameRenderer:
    def __init__( self, fieldSize: glm.ivec3 ):
        self._fieldSize = fieldSize
        self._vao_blank = glGenVertexArrays( 1 )
        self._velocityLineProgramInfo = BuildPipelineProgram( glsw.v, glsw.f, ( "GRID",) )
        self._sceneBoxWireProgramInfo = BuildPipelineProgram( glsw.v, glsw.f, ( "SCENEBOX", "LINE" ) )
        self._sceneBoxSurfProgramInfo = BuildPipelineProgram( glsw.v, glsw.f, ( "SCENEBOX", "SURF" ) )
        self._depthInteractionBuffer  = OffScreenDepthFramebuffer()

        with uglw.ProgBound( self._velocityLineProgramInfo.__progHandle__ ):
            glUniform3iv( self._velocityLineProgramInfo.gridN, 1, list( fieldSize ) )

        self._tex_velocity = glGenTextures( 1 )
        with uglw.TextureBound( GL_TEXTURE_2D, self._tex_velocity ):
            glTexImage2D( GL_TEXTURE_2D, 0, GL_RG32F, fieldSize.x, fieldSize.y, 0, GL_RG,
                          GL_FLOAT, 0 ) # don't care input data
            uglw.TextureMinMaxNEAREST( GL_TEXTURE_2D )

    def __del__(self):
        glDeleteVertexArrays( [ self._vao_blank ] )
        glDeleteProgram( self._velocityLineProgramInfo.__progHandle__ )
        glDeleteProgram( self._sceneBoxWireProgramInfo.__progHandle__ )
        del self._depthInteractionBuffer

    def RenderToDrawBuffer_VelocityLine ( self, vpMat: glm.mat4,
        velocity2DField2D: Vec2DField2D, fieldSpacing: float
    ):
        with uglw.VAOBound( self._vao_blank ):
            with uglw.TextureBound( GL_TEXTURE_2D, self._tex_velocity ):
                glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, self._fieldSize.x, self._fieldSize.y, GL_RG, GL_FLOAT,
                                 velocity2DField2D.GetRawData() )

                with uglw.ProgBound( self._velocityLineProgramInfo.__progHandle__ ):
                    cellNx2 = self._fieldSize.x *self._fieldSize.y *self._fieldSize.z *2

                    glUniform1fv( self._velocityLineProgramInfo.gridSpacing, 1, fieldSpacing )
                    glUniformMatrix4fv( self._velocityLineProgramInfo.vpMat, 1, GL_FALSE, list( vpMat ) )
                    glDrawArrays( GL_LINES, 0, cellNx2 )
                    glDrawArrays( GL_POINTS, 0, cellNx2 )

    def RenderToDrawBuffer_SceneBoxWire ( self, vpMat: glm.mat4, boxSize: glm.vec3 ):
        with uglw.VAOBound( self._vao_blank ):
            with uglw.ProgBound( self._sceneBoxWireProgramInfo.__progHandle__ ):
                glUniform3fv( self._sceneBoxWireProgramInfo.boxSize, 1, list( boxSize ) )
                glUniformMatrix4fv( self._sceneBoxWireProgramInfo.vpMat, 1, GL_FALSE, list( vpMat ) )
                glDrawArrays( GL_LINES, 0, 24 )

    def GetSceneBoxCursorIntersection (
        self, vpMat: QMatrix4x4, boxSize: QVector3D, winspaceCursorPos: QPoint, winspaceDimension
    )-> QVector3D:
        """
        :param winspaceCursorPos: lower-left corner as origin
        :return: 3D world position of cursor interaction
        """
        self._depthInteractionBuffer.RequestBindFBO( winspaceDimension )

        glClearBufferfv( GL_DEPTH, 0, ( 1., ) )

        with uglw.VAOBound( self._vao_blank ):
            with uglw.ProgBound( self._sceneBoxSurfProgramInfo.__progHandle__ ):
                glUniform3fv( self._sceneBoxSurfProgramInfo.boxSize, 1, utyp.GetTuple( boxSize ) )
                glUniformMatrix4fv( self._sceneBoxSurfProgramInfo.vpMat, 1, GL_FALSE, vpMat.data() )
                glDrawArrays( GL_TRIANGLES, 0, 3 *2 *6 )

        glBindFramebuffer( GL_FRAMEBUFFER, 0 )
        print( winspaceCursorPos )


