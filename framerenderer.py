"As noted"

from OpenGL.GL import *
import glm

"""All method must be invoked in the same living OpenGL 3.3 context"""
class FrameRenderer:
    def __init__( self ):

        # analogue to OGLSuperBible Listing 2.5
        vertShader = glCreateShader( GL_VERTEX_SHADER )
        glShaderSource( vertShader, [ _velocityLineVertShader ] )
        glCompileShader( vertShader )

        fragShader = glCreateShader( GL_FRAGMENT_SHADER )
        glShaderSource( fragShader, [ _velocityLineFragShader ] )
        glCompileShader( fragShader )

        if glGetShaderiv( vertShader, GL_COMPILE_STATUS ) != GL_TRUE:
            print ( glGetShaderInfoLog( vertShader ) )
        if glGetShaderiv( fragShader, GL_COMPILE_STATUS ) != GL_TRUE:
            print ( glGetShaderInfoLog( fragShader ) )

        program = glCreateProgram()
        glAttachShader( program, vertShader )
        glAttachShader( program, fragShader )
        glLinkProgram( program )

        if glGetProgramiv( program, GL_LINK_STATUS ) != GL_TRUE:
            print ( glGetProgramInfoLog( program ) )

        glDeleteShader( vertShader )
        glDeleteShader( fragShader )

        blankVao = glGenVertexArrays( 1 )

        self.program = program
        self.blankVao = blankVao

    def __del__(self):
        pass # will do

    def RenderToDrawBuffer_VelocityLine ( self, drawBufferSize: glm.ivec2, camMat: glm.mat4 ):

        glClearBufferfv( GL_COLOR, 0, ( 1,.5,.5,1 ) )

        glPointSize( 2.0 )

        glUseProgram( self.program )

        glBindVertexArray( self.blankVao )
        glDrawArrays( GL_LINES, 0, 100*2 )
        glBindVertexArray( 0 )

_velocityLineVertShader = """
#version 330 core
#line 58

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

void main ( void ) {
    int     cellID = int( gl_VertexID *0.5 );
    bool    isTail  = mod( gl_VertexID, 2 ) == 0.0; // isOdd 0---->1

    vec3    gridSize    = gridSpacing *gridN;
    ivec3   gridCoord   = GetIndex3Dfrom1D( cellID, gridN.xy );
    vec3    gridPos     = ( gridSize *gridCoord ) / gridN;
    vec3    centeredGridPos = gridPos -( 0.5 *gridSpacing *( gridN -1 ) );

    if ( isTail ) {
        centeredGridPos += 0.05;
    }

    gl_Position = vec4( centeredGridPos, 1 );
}
"""

_velocityLineFragShader = """
#version 330 core

out vec4 color;

void main ( void ) {
    color = vec4( 0, 0.8, 1.0, 1.0 );
}
"""