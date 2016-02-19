"As noted"

from OpenGL.GL import *
import glm

from sleepy_mockup_glslsampler import *
from glsl_wrangler import BuildPipelineProgram
import glsw_scenebox


def CompileShaderProgram( vertShaderSrc: str, fragShaderSrc: str )-> GLhandle:
    # analogue to OGLSuperBible Listing 2.5
    vertShader = glCreateShader( GL_VERTEX_SHADER )
    glShaderSource( vertShader, [ vertShaderSrc ] )
    glCompileShader( vertShader )

    fragShader = glCreateShader( GL_FRAGMENT_SHADER )
    glShaderSource( fragShader, [ fragShaderSrc ] )
    glCompileShader( fragShader )

    if glGetShaderiv( vertShader, GL_COMPILE_STATUS ) != GL_TRUE:
        print ( glGetShaderInfoLog( vertShader ) )
        print ( "here the shader", vertShaderSrc )
    if glGetShaderiv( fragShader, GL_COMPILE_STATUS ) != GL_TRUE:
        print ( glGetShaderInfoLog( fragShader ) )
        print ( "here the shader", fragShaderSrc )

    program = glCreateProgram()
    glAttachShader( program, vertShader )
    glAttachShader( program, fragShader )
    glLinkProgram( program )

    if glGetProgramiv( program, GL_LINK_STATUS ) != GL_TRUE:
        print ( glGetProgramInfoLog( program ) )

    glDeleteShader( vertShader )
    glDeleteShader( fragShader )

    return program


"""All method must be invoked in the same living OpenGL 3.3 context"""
class FrameRenderer:
    def __init__( self, fieldSize: glm.ivec3 ):
        self._velocityLineProgram = CompileShaderProgram( _velocityLineVertShader, _opaqueShadelessFragShader )
        self._sceneBoxWireProgramInfo = BuildPipelineProgram( glsw_scenebox, '330 core', "TEST" )
        self._vao_blank = glGenVertexArrays( 1 )
        self._fieldSize = fieldSize

        glUseProgram( self._velocityLineProgram )
        glUniform3iv( glGetUniformLocation( self._velocityLineProgram, 'gridN' ), 1, list( fieldSize ) )
        glUseProgram( 0 )

        self._tex_velocity = glGenTextures( 1 )
        glBindTexture( GL_TEXTURE_2D, self._tex_velocity )
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RG32F, fieldSize.x, fieldSize.y, 0, GL_RG,
            GL_FLOAT, 0 # don't care input data
        )
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST )
        glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST )
        glBindTexture( GL_TEXTURE_2D, 0 )

    def __del__(self):
        glDeleteProgram( self._velocityLineProgram )
        glDeleteProgram( self._sceneBoxWireProgramInfo.__progHandle__ )
        glDeleteVertexArrays( [ self._vao_blank ] )

    def RenderToDrawBuffer_VelocityLine ( self, vpMat: glm.mat4,
        velocity2DField2D: Vec2DField2D, fieldSpacing: float
    ):
        glBindVertexArray( self._vao_blank )
        glBindTexture( GL_TEXTURE_2D, self._tex_velocity )

        glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, self._fieldSize.x, self._fieldSize.y, GL_RG, GL_FLOAT, velocity2DField2D.GetRawData() )

        glUseProgram( self._velocityLineProgram )

        glUniform1fv( glGetUniformLocation( self._velocityLineProgram, 'gridSpacing' ), 1, fieldSpacing )
        glUniformMatrix4fv( glGetUniformLocation( self._velocityLineProgram, 'vpMat' ), 1, GL_FALSE, list( vpMat ) )
        cellNx2 = self._fieldSize.x *self._fieldSize.y *self._fieldSize.z *2
        glDrawArrays( GL_LINES, 0, cellNx2 )
        glDrawArrays( GL_POINTS, 0, cellNx2 )

        glUseProgram( 0 )

        glBindTexture( GL_TEXTURE_2D, 0 )
        glBindVertexArray( 0 )

    def RenderToDrawBuffer_SceneBoxWire ( self, vpMat: glm.mat4, boxSize: glm.vec3 ):
        glBindVertexArray( self._vao_blank )
        glUseProgram( self._sceneBoxWireProgramInfo.__progHandle__ )

        glUniform3fv( self._sceneBoxWireProgramInfo.boxSize, 1, list( boxSize ) )
        glUniformMatrix4fv( self._sceneBoxWireProgramInfo.vpMat, 1, GL_FALSE, list( vpMat ) )
        glDrawArrays( GL_LINES, 0, 24 )

        glUseProgram( 0 )
        glBindVertexArray( 0 )

    def GetSceneBoxCursorIntersection ( self, vpMat: glm.mat4, boxSize: glm.vec3, screenspaceCursorPos: glm.ivec2 )-> glm.vec3:
        pass


_velocityLineVertShader = """
#version 330 core
#line 71

/* confuse how, but taken from here:
 * http://stackoverflow.com/questions/14845084/how-do-i-convert-a-1d-index-into-a-3d-index
 * look like author tell it wrong ( round -> floor ) */
ivec3 GetIndex3Dfrom1D( int i, ivec2 wh ) {
    int     wXh     = wh.x *wh.y;
    float   rWxH    = 1.0 /wXh;
    float   rW      = 1.0 /wh.x;
    int z = int( i *rWxH );
    int y = int( ( i -z*wXh ) *rW );
    int x = i -wh.x *( y +wh.y*z );
    return ivec3( x, y, z );
}

// unit: meter
uniform float gridSpacing = 0.1;
uniform ivec3 gridN = ivec3( 10 );

// camera
uniform mat4 vpMat = mat4( 1 );

// field
uniform sampler2D velocityField;

void main ( void ) {
    int     cellID = int( gl_VertexID *0.5 );
    bool    isTail  = mod( gl_VertexID, 2 ) == 0.0; // isOdd 0---->1

    vec3    gridSize            = gridSpacing *gridN;
    vec3    gridCenterPos       = 0.5 *gridSpacing *( gridN -1 );

    ivec3   cellCoord           = GetIndex3Dfrom1D( cellID, gridN.xy );
    vec3    gridScaledCellPos   = ( gridSize *cellCoord ) / gridN;
    vec3    gridGroundCenteredCellPos = gridScaledCellPos -gridCenterPos;

    if ( isTail ) {
        gridGroundCenteredCellPos += vec3( texelFetch( velocityField, cellCoord.xy, 0 ).xy, 0 );
    }

    gl_Position = vpMat *vec4( gridGroundCenteredCellPos, 1 );
}
"""

_opaqueShadelessFragShader = """
#version 330 core
#line 139

out vec4 color;

void main ( void ) {
    color = vec4( 0.044, 0.687, 0.800, 1.0 );
}
"""