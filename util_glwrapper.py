from contextlib import contextmanager
from OpenGL.GL import *

# for using with "with statement", see The Python Lib Ref: 29.6.1 > @contextlib.contextmanager
@contextmanager
def VAOBound( vaoName ): glBindVertexArray( vaoName ); yield; glBindVertexArray( 0 );

@contextmanager
def ProgBound( progName ): glUseProgram( progName ); yield; glUseProgram( 0 );

@contextmanager
def TextureBound( target, texName ): glBindTexture( target, texName ); yield; glBindTexture( target, 0 )

def TextureMinMaxNEAREST( target ):
    glTexParameteri( target, GL_TEXTURE_MIN_FILTER, GL_NEAREST )
    glTexParameteri( target, GL_TEXTURE_MAG_FILTER, GL_NEAREST )