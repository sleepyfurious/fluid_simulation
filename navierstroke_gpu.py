import typing as T
from    OpenGL.GL import *
from    PyQt5.QtCore import QPoint
from    PyQt5.QtGui import QVector3D

import  util_glwrapper          as uglw
import  util_datatype           as utyp
from    util_glshaderwrangler   import DefineGLSLShaderProgram, BuildPipelineProgram


class Harris2004NavierStrokeSimulation:

    def __init__( self, gridSize: T.Tuple[int,int,int], gridSpacing ):
        ONE_3D = QVector3D(1,1,1)

        self._tex_uNaux3p1_0, self._tex_uNaux3p1_1, self._tex_uNaux3eqTenR1 \
            = _GenAllocateTexturesRGBA32F3DEdgeclamp( gridSize, 3 )

        self._vao_blank         = glGenVertexArrays( 1 )
        self._fboName           = glGenFramebuffers( 1 )
        self._iprog_advection   = BuildPipelineProgram( _vert, _frag, ( "ADVECTION",) )
        self._iprog_force       = BuildPipelineProgram( _vert, _frag, ( "FORCE",) )

        self._gridSizeZ         = gridSize[2]
        self._rGridspace        = 1 /gridSpacing
        self.gridSpacing = gridSpacing
        self.gridSize = gridSize

        rGridsize = ONE_3D /QVector3D( *gridSize )

        with uglw.ProgBound( self._iprog_advection.__progHandle__ ):
            glUniform3fv( self._iprog_advection.rGridsize, 1, utyp.GetTuple( rGridsize ) )
        with uglw.ProgBound( self._iprog_force.__progHandle__ ):
            glUniform1fv( self._iprog_force.rGridspace, 1, 1 /gridSpacing  )
            glUniform1fv( self._iprog_force.rUnitcellspaceBrushsize, 1, 1 /4  )
            glUniform3fv( self._iprog_force.unitcellspaceCursorPosition, 1, ( 5, 5, self._gridSizeZ -1 -5 )  )

        self._uNaux_texSlabingID = 0
        self._uNaux_texSlabingDict = { 0: self._tex_uNaux3p1_0, 1: self._tex_uNaux3p1_1, 2: self._tex_uNaux3eqTenR1 }
        with uglw.FBOBound( self._fboName ): self._Step_ClearGridAs0( self._GetOffsetSlabingUnauxTexname( 0 ) )

        self._devTmp_stepCnt = 0

    def __del__(self):
        glDeleteVertexArrays( [ self._vao_blank ] )
        glDeleteFramebuffers( [ self._fboName ] )
        glDeleteProgram( self._iprog_advection.__progHandle__ )
        glDeleteProgram( self._iprog_force.__progHandle__ )

    def _GetNextSlabingUnauxTexname( self )-> GLuint:
        self._uNaux_texSlabingID = ( self._uNaux_texSlabingID +1 ) %3
        return self._uNaux_texSlabingDict[ self._uNaux_texSlabingID ]

    def _GetOffsetSlabingUnauxTexname( self, offset: int ):
        return self._uNaux_texSlabingDict[ (self._uNaux_texSlabingID +offset) %3 ]

    def Step( self, deltaT: float ):
        print ( self._devTmp_stepCnt )

        glBindVertexArray( self._vao_blank )
        glBindFramebuffer( GL_FRAMEBUFFER, self._fboName )
        # self._Step_ClearGridAs0( self._GetOffsetSlabingUnauxTexname( 0 ) ) # Temp, reset last step

        glUseProgram( self._iprog_advection.__progHandle__ )
        glBindTexture( GL_TEXTURE_3D, self._GetOffsetSlabingUnauxTexname( 0 ) )
        glUniform1fv( self._iprog_advection.dtXrGridspace, 1, self._rGridspace )
        self._Step_ComputeGrid_PreProgVaoBind( self._iprog_advection, self._GetNextSlabingUnauxTexname() )

        with uglw.EnableScope( GL_BLEND ):
            glBlendFunc( GL_ONE, GL_ONE ) #additive blend
            glUseProgram( self._iprog_force.__progHandle__ )
            force = QVector3D( 20, 20, -20 ) if self._devTmp_stepCnt < 500 and self._devTmp_stepCnt > 1 else QVector3D()
            glUniform3fv( self._iprog_force.forceXdt, 1, utyp.GetTuple( force *deltaT ) )
            self._Step_ComputeGrid_PreProgVaoBind( self._iprog_force, self._GetOffsetSlabingUnauxTexname( 0 ) )

        glBindTexture( GL_TEXTURE_3D, 0 )
        glUseProgram( 0 )
        glBindFramebuffer( GL_FRAMEBUFFER, 0 )
        glBindVertexArray( 0 )

        self._devTmp_stepCnt += 1

    def _Step_ClearGridAs0( self, targetTexname ):
        for operating_z in range( self._gridSizeZ ):
            _BindFBOwithTex3DatLayer( targetTexname, operating_z )
            glClearBufferfv( GL_COLOR, 0, (0,0,0,0) )

    def _Step_ComputeGrid_PreProgVaoBind( self, prog, targetTexname ):
        for operating_z in range( self._gridSizeZ ):
            glUniform1i( prog.operating_z, operating_z )
            _BindFBOwithTex3DatLayer( targetTexname, operating_z )
            glDrawArrays( GL_TRIANGLES, 0, 6 )

    def GetTexnameOfCurrentVelocityField( self )-> GLuint:
        return self._GetOffsetSlabingUnauxTexname( 0 )


def _GenAllocateTexturesRGBA32F3DEdgeclamp( size: T.Tuple[ int, int, int ], count ):
    maxGridSize = glGetIntegerv( GL_MAX_3D_TEXTURE_SIZE )
    if  any( map( lambda x: x > maxGridSize, size ) ) or any( map( lambda x: x < 1, size ) ):
        raise AssertionError # input size not applicable

    texNames = glGenTextures( count )

    for texName in texNames:
        with uglw.TextureBound( GL_TEXTURE_3D, texName ):
            glTexImage3D( GL_TEXTURE_3D, 0, GL_RGBA32F, size[0], size[1], size[2], 0, GL_RGBA,
                          GL_FLOAT, 0 ) # don't care uploading anything
            uglw.SetTextureMinMaxFilter( GL_TEXTURE_3D, GL_LINEAR )
            glTexParameteri( GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE )
            glTexParameteri( GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE )
            glTexParameteri( GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE )

    return texNames

def _BindFBOwithTex3DatLayer( texName, layer ):
    glFramebufferTextureLayer( GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texName, 0, layer )

_frag = DefineGLSLShaderProgram( GL_FRAGMENT_SHADER, 'navierstroke term operation', """
layout(pixel_center_integer) in vec4 gl_FragCoord;
uniform int  operating_z;

out     vec4 outVar;

#if/**/ defined( ADVECTION )
    uniform sampler3D   u3_1;
    uniform vec3        rGridsize;
    uniform float       dtXrGridspace;

 #elif  defined( JACOBI )
    uniform sampler3D   _3p1, _3eqTen1;

 #elif  defined( FORCE )
    uniform float       rGridspace,
                        rUnitcellspaceBrushsize;
    uniform vec3        unitcellspaceCursorPosition,
                        forceXdt;

 #elif  defined( DIVERGENCE )
    uniform sampler3D   u3_1;

 #elif  defined( GRADIENTSUB )
    uniform sampler3D   u3_1, _3p1;

 #endif

 void main ( void ) {
#if/**/ defined( ADVECTION )
    ivec3 unitcellspaceCoord    = ivec3( gl_FragCoord.xy, operating_z );

    vec3 unitcellspaceFromPos   = vec3( unitcellspaceCoord ) -dtXrGridspace *vec3(texelFetch( u3_1, unitcellspaceCoord, 0 ));
    vec3 texspaceFromPos        = ( unitcellspaceFromPos +0.5 ) *rGridsize;

    outVar = texture( u3_1, texspaceFromPos );

 #elif  defined( FORCE )
    vec3 unitcellspaceCursorVec = vec3( gl_FragCoord.xy, operating_z ) *rGridspace -unitcellspaceCursorPosition;
    float lengthSqUnitcellspaceCursorVec = unitcellspaceCursorVec.x *unitcellspaceCursorVec.x
                                         + unitcellspaceCursorVec.y *unitcellspaceCursorVec.y
                                         + unitcellspaceCursorVec.z *unitcellspaceCursorVec.z;

    outVar.xyz = forceXdt *exp( -lengthSqUnitcellspaceCursorVec *rUnitcellspaceBrushsize );

 #endif

 }
""" )

_vert = DefineGLSLShaderProgram( GL_VERTEX_SHADER, 'navierstroke scr quad', """
const vec2 QUAD_VERTICES[4] = vec2[4]( vec2( 1, 1 ), vec2(-1, 1 ), vec2(-1,-1 ), vec2( 1,-1 ) );
const int  QUAD_TRIANGLESIDX[ 3 *2 ] = int[ 3 *2 ]( 0, 1, 3,  3, 1, 2 );

void main ( void ) {
    gl_Position = vec4( QUAD_VERTICES[ QUAD_TRIANGLESIDX[ gl_VertexID ] ], 0, 1 );
}
""" )
