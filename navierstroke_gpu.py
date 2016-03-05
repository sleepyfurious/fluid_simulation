import typing as T
from    OpenGL.GL import *
from    PyQt5.QtGui import QVector3D

import  util_glwrapper          as uglw
import  util_datatype           as utyp
from    util_glshaderwrangler   import BuildPipelineProgram

import  navierstroke_glsw       as glsw

class _SlabingTexture:
    def __init__( self, gridSize: T.Tuple[int,int,int] ):
        maxGridSize = glGetIntegerv( GL_MAX_3D_TEXTURE_SIZE )
        if  any( map( lambda x: x > maxGridSize, gridSize ) ) or any( map( lambda x: x < 1, gridSize ) ):
            raise AssertionError # input size not applicable

        # GenAllocateTexturesRGBA32F3D with Edgeclamping
        self._tex_uNaux3p1_0, self._tex_uNaux3p1_1, self._tex_uNaux3eqTenR1 = texNames = glGenTextures( 3 )

        for texName in texNames:
            with uglw.TextureBound( GL_TEXTURE_3D, texName ):
                glTexImage3D( GL_TEXTURE_3D, 0, GL_RGBA32F, gridSize[0], gridSize[1], gridSize[2], 0, GL_RGBA,
                              GL_FLOAT, 0 ) # don't care uploading anything
                uglw.SetTextureMinMaxFilter( GL_TEXTURE_3D, GL_LINEAR )
                glTexParameteri( GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE )
                glTexParameteri( GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE )
                glTexParameteri( GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE )

        self._uNaux_texSlabingID = 0
        self._uNaux_texSlabingDict = { 0: self._tex_uNaux3p1_0, 1: self._tex_uNaux3p1_1, 2: self._tex_uNaux3eqTenR1 }

        self.__3p1_texSlabingID = 0
        self.__3p1_texSlabingDict = { 0: self._tex_uNaux3p1_0, 1: self._tex_uNaux3p1_1 }

    def GetNextSlabingUnaux3_1Texname( self )-> GLuint:
        self._uNaux_texSlabingID = ( self._uNaux_texSlabingID +1 ) %len( self._uNaux_texSlabingDict )
        return self._uNaux_texSlabingDict[ self._uNaux_texSlabingID ]

    def GetOffsetSlabingUnaux3_1Texname( self, offset: int )-> GLuint:
        return self._uNaux_texSlabingDict[ (self._uNaux_texSlabingID +offset) %len( self._uNaux_texSlabingDict ) ]

    def GetNextSlabing_3p1Texname( self )-> GLuint:
        self.__3p1_texSlabingID = ( self.__3p1_texSlabingID +1 ) %len( self.__3p1_texSlabingDict )
        return self.__3p1_texSlabingDict[ self.__3p1_texSlabingID ]

    def GetCurrentSlabing_3p1Texname( self )-> GLuint:
        return self.__3p1_texSlabingDict[ self.__3p1_texSlabingID ]

    def Get_3EqTenR1Texname( self )-> GLuint: return self._tex_uNaux3eqTenR1


class Harris2004NavierStrokeSimulation:

    def __init__( self, gridSize: T.Tuple[int,int,int], gridSpacing ):
        ONE_3D = QVector3D(1,1,1)

        self._tex               = _SlabingTexture( gridSize )

        self._vao_blank         = glGenVertexArrays( 1 )
        self._fboName           = glGenFramebuffers( 1 )
        self._iprog_advection   = BuildPipelineProgram( glsw.v, glsw.f, ( "ADVECTION",) )
        self._iprog_force       = BuildPipelineProgram( glsw.v, glsw.f, ( "FORCE",) )
        self._iprog_divergence  = BuildPipelineProgram( glsw.v, glsw.f, ( "DIVERGENCE",) )
        self._iprog_jacobi      = BuildPipelineProgram( glsw.v, glsw.f, ( "JACOBI",) )
        self._iprog_gradsub     = BuildPipelineProgram( glsw.v, glsw.f, ( "GRADIENTSUB",) )

        self._gridSize          = gridSize
        self._rGridspacing      = 1 / gridSpacing
        self._pressureJacobiIteration = 40 # [40,80]

        rGridsize = ONE_3D /QVector3D( *gridSize )

        with uglw.ProgBound( self._iprog_advection.__progHandle__ ):
            glUniform3fv( self._iprog_advection.rGridsize, 1, utyp.GetTuple( rGridsize ) )

        with uglw.ProgBound( self._iprog_force.__progHandle__ ):
            glUniform1fv( self._iprog_force.rUnitcellspaceHalfBrushsize, 1, 1 /( 0.5 *1 )  )
            glUniform3fv( self._iprog_force.unitcellspaceCursorPosition, 1, ( 5, 5, self._gridSize[2] -1 -5 ) )

        halfRgridspacing = 0.5 *self._rGridspacing
        with uglw.ProgBound( self._iprog_divergence.__progHandle__ ):
            glUniform1fv( self._iprog_divergence.halfRgridspacing, 1, halfRgridspacing )
        with uglw.ProgBound( self._iprog_gradsub.__progHandle__ ):
            glUniform1fv( self._iprog_gradsub.halfRgridspacing, 1, halfRgridspacing )

        with uglw.ProgBound( self._iprog_jacobi.__progHandle__ ):
            glUniform2fv( self._iprog_jacobi.alphaRbeta, 1, ( -gridSpacing *gridSpacing, 1 /4 ) )

        with uglw.FBOBound( self._fboName ): self._Step_ClearGridAs0( self._tex.GetOffsetSlabingUnaux3_1Texname( 0 ) )
        with uglw.FBOBound( self._fboName ): self._Step_ClearGridAs0( self._tex.GetOffsetSlabingUnaux3_1Texname( 1 ) )
        with uglw.FBOBound( self._fboName ): self._Step_ClearGridAs0( self._tex.GetOffsetSlabingUnaux3_1Texname( 2 ) )

        self._devTmp_stepCnt = 0

    def __del__(self):
        glDeleteVertexArrays( [ self._vao_blank ] )
        glDeleteFramebuffers( [ self._fboName ] )
        glDeleteProgram( self._iprog_advection.__progHandle__ )
        glDeleteProgram( self._iprog_force.__progHandle__ )

    def Step( self, deltaT: float ):
        print ( self._devTmp_stepCnt )

        glBindVertexArray( self._vao_blank )
        glBindFramebuffer( GL_FRAMEBUFFER, self._fboName )
        # self._Step_ClearGridAs0( self._tex.GetOffsetSlabingUnaux3_1Texname( 0 ) ) # Temp, reset last step

        glViewport( 1, 1, self._gridSize[0] -2, self._gridSize[1] -2 )

        # ADVECTION
        glUseProgram( self._iprog_advection.__progHandle__ )
        glBindTexture( GL_TEXTURE_3D, self._tex.GetOffsetSlabingUnaux3_1Texname( 0 ) )
        glUniform1fv( self._iprog_advection.dtXrGridspacing, 1, self._rGridspacing )
        self._Step_ExecInnerGrid_PreProgVaoBind( self._iprog_advection, self._tex.GetNextSlabingUnaux3_1Texname( ) )

        # ADD FORCE
        with uglw.EnableScope( GL_BLEND ):
            glBlendFunc( GL_ONE, GL_ONE ) #additive blend
            glUseProgram( self._iprog_force.__progHandle__ )
            force = QVector3D( 20, 20, 0 ) if self._devTmp_stepCnt < 500 and self._devTmp_stepCnt > 1 else QVector3D()
            glUniform3fv( self._iprog_force.forceXdt, 1, utyp.GetTuple( force *deltaT ) )
            self._Step_ExecInnerGrid_PreProgVaoBind( self._iprog_force, self._tex.GetOffsetSlabingUnaux3_1Texname( 0 ) )

        glColorMask( GL_FALSE, GL_FALSE, GL_FALSE, GL_TRUE )

        # PROJECTION DIVERGENCE
        glUseProgram( self._iprog_divergence.__progHandle__ )
        glBindTexture( GL_TEXTURE_3D, self._tex.GetOffsetSlabingUnaux3_1Texname( 0 ) )
        self._Step_ExecInnerGrid_PreProgVaoBind( self._iprog_divergence, self._tex.Get_3EqTenR1Texname( ) )

        # PROJECTION JACOBI
        glUseProgram( self._iprog_jacobi.__progHandle__ )
        for i in range( self._pressureJacobiIteration ):
            glActiveTexture( GL_TEXTURE1 ); glBindTexture( GL_TEXTURE_3D, self._tex.Get_3EqTenR1Texname() )
            glActiveTexture( GL_TEXTURE0 ); glBindTexture( GL_TEXTURE_3D, self._tex.GetCurrentSlabing_3p1Texname() )
            self._Step_ExecInnerGrid_PreProgVaoBind( self._iprog_jacobi, self._tex.GetNextSlabing_3p1Texname( ) )

        glColorMask( GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE )

        # PROJECTION GRADIENT SUBTRACTION
        glUseProgram( self._iprog_gradsub.__progHandle__ )
        glActiveTexture( GL_TEXTURE1 ); glBindTexture( GL_TEXTURE_3D, self._tex.GetCurrentSlabing_3p1Texname() )
        glActiveTexture( GL_TEXTURE0 ); glBindTexture( GL_TEXTURE_3D, self._tex.GetOffsetSlabingUnaux3_1Texname( 0 ) )
        self._Step_ExecInnerGrid_PreProgVaoBind( self._iprog_gradsub, self._tex.GetNextSlabingUnaux3_1Texname( ) )

        glColorMask( GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE )

        glActiveTexture( GL_TEXTURE1 ); glBindTexture( GL_TEXTURE_3D, 0 )
        glActiveTexture( GL_TEXTURE0 ); glBindTexture( GL_TEXTURE_3D, 0 )
        glUseProgram( 0 )
        glBindFramebuffer( GL_FRAMEBUFFER, 0 )
        glBindVertexArray( 0 )

        self._devTmp_stepCnt += 1

    def _Step_ClearGridAs0( self, targetTexname ):
        for operating_z in range( self._gridSize[2] ):
            _BindFBOwithTex3DatLayer( targetTexname, operating_z )
            glClearBufferfv( GL_COLOR, 0, (0,0,0,0) )

    def _Step_ExecInnerGrid_PreProgVaoBind( self, prog, targetTexname ):
        for operating_z in range( 1, self._gridSize[2] -1 ):
            glUniform1i( prog.operating_z, operating_z )
            _BindFBOwithTex3DatLayer( targetTexname, operating_z )
            glDrawArrays( GL_TRIANGLES, 0, 6 )

    def GetTexnameOfCurrentVelocityField( self )-> GLuint:
        return self._tex.GetOffsetSlabingUnaux3_1Texname( 0 )


def _BindFBOwithTex3DatLayer( texName, layer ):
    glFramebufferTextureLayer( GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texName, 0, layer )