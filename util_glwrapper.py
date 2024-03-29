from contextlib import contextmanager
from OpenGL.GL import *

# for using with "with statement", see The Python Lib Ref: 29.6.1 > @contextlib.contextmanager
@contextmanager
def VAOBound( vaoName ): glBindVertexArray( vaoName ); yield; glBindVertexArray( 0 );

@contextmanager
def ProgBound( progName ): glUseProgram( progName ); yield; glUseProgram( 0 );

@contextmanager
def TextureBound( target, texName ): glBindTexture( target, texName ); yield; glBindTexture( target, 0 )

@contextmanager
def FBOBound( fboName ): glBindFramebuffer( GL_FRAMEBUFFER, fboName ); yield; glBindFramebuffer( GL_FRAMEBUFFER, 0 )

@contextmanager
def EnableScope( stateName ): glEnable( stateName ); yield; glDisable( stateName )

def SetTextureMinMaxFilter( target, filter ):
    glTexParameteri( target, GL_TEXTURE_MIN_FILTER, filter )
    glTexParameteri( target, GL_TEXTURE_MAG_FILTER, filter )