from PyQt5.QtCore   import QPoint
from OpenGL.GL      import *

import util_glwrapper as uglw

"""create depth-only FBO with texture and enlarge when require"""
class OffScreenDepthFramebuffer:
    def __init__(self):
        self._allocatedSize = QPoint()
        self._fboName = 0
        self._texname = 0

    def __del__(self):
        glDeleteFramebuffers( [ self._fboName ] )
        glDeleteTextures( [ self._texname ] )

    def RequestBindFBO(self, targetSize: QPoint ):
        if self._fboName == 0: self._fboName = glGenFramebuffers( 1 )

        if self._allocatedSize != targetSize:
            glDeleteTextures( [ self._texname ] )

            self._texname = glGenTextures( 1 )
            with uglw.TextureBound( GL_TEXTURE_2D, self._texname ):
                glTexImage2D( GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32F,
                              targetSize.x(), targetSize.y(), 0, GL_DEPTH_COMPONENT,
                              GL_FLOAT, 0 ) # don't care these last 2 param for input data

            with uglw.FBOBound( self._fboName ):
                glFramebufferTexture( GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, self._texname, 0 )
                glDrawBuffer(GL_NONE)
                glReadBuffer(GL_NONE)

                if glCheckFramebufferStatus( GL_DRAW_FRAMEBUFFER ) != GL_FRAMEBUFFER_COMPLETE:
                    print( "ERROR: Offscreen Buffer Incomplete" )

            self._allocatedSize = targetSize

        glBindFramebuffer( GL_FRAMEBUFFER, self._fboName )
