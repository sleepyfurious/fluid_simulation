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

        glPointSize( 40.0 )

        glUseProgram( self.program )

        glBindVertexArray( self.blankVao )
        glDrawArrays( GL_POINTS, 0, 1 )
        glBindVertexArray( 0 )

_velocityLineVertShader = """
#version 330 core

void main ( void ) {
    gl_Position = vec4( 0, 0, 0.5, 1 );
}
"""

_velocityLineFragShader = """
#version 330 core

out vec4 color;

void main ( void ) {
    color = vec4( 0, 0.8, 1.0, 1.0 );
}
"""