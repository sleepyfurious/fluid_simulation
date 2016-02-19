# I simplify and borrow The Little Grasshopper’s Lua shader wrangler to handle my shader management (a primal one). see: http://prideout.net/blog/?p=1
#
# chosen concept:
# - function to automate a generation of glsl source code as a global variable of a file
# - line inspection with ‘#line’ preprocessor directive prepending
#
# my target feature:
# - prepend preprocessor directive
# - auto build a simple vert-frag pipeline
# - return an object that populated with program's handle and active uniform's location
#
## USAGE EXAMPLE #######################################################################################################
#
# Define shaders of a whole pipeline in a file like this:
#
# // START OF A SAMPLE ILLUSTRATION SHADER FILE
#
# DefineGLSLShaderProgram( GL_VERTEX_SHADER, """
# void main ( void ) {
# ...
# }
# """ )
#
# DefineGLSLShaderProgram( GL_FRAGMENT_SHADER, """
# uniform vec3 çolor;
# out vec4 outputColor;
#
# void main ( void ) {
#     outputColor = color;
# }
# """ )
#
# // END OF THE SHADER FILE
#
# this have to be run in GL context for program client:
#  programInfo = BuildPipelineProgram( sys.modules[__name__] , "330 core", ( 'define test', ) )
#
# this is the OpenGl's handle
#  programInfo.__progHandle__
#
# this is the uniform location of the color variable from our example
#  programInfo.color


import inspect
from array import array
from OpenGL.GL import *

_glStageToVarName = { GL_VERTEX_SHADER: '__vert__', GL_FRAGMENT_SHADER: '__frag__' }

def DefineGLSLShaderProgram( stage, sourcecode ):
    callerFrameInfo = inspect.getouterframes( inspect.currentframe() )[1] #type: inspect.FrameInfo
    sourcecodelineN = sourcecode.count('\n') +1

    # append the source string as a variable to caller's global dictionary (using caller inspection).
    # see: http://stackoverflow.com/questions/3711184/how-to-use-inspect-to-get-the-callers-info-from-callee-in-python
    callerFrameInfo.frame.f_globals[ _glStageToVarName[ stage ] ] = \
        '#line ' +str( callerFrameInfo.lineno -sourcecodelineN +2 ) \
        + sourcecode

class ProgramInfo:
    def __init__( self, progHandle ):
        self.__progHandle__ = progHandle

def _PrependPreProc( shaderSource, tupleOfOrderedPreprocDirectives ):
    prependedStr = ''.join( [ '#define ' + item +'\n' for item in tupleOfOrderedPreprocDirectives ] )
    return prependedStr +shaderSource


def BuildPipelineProgram( definitionModule, versionStr: str, tupleOfOrderedPreprocDirectives )-> ProgramInfo:
    """build OpenGL Program Pipeline in current GL context.

    Return ProgramInfo that contain attribute progHandle that is GL's handle. beware to build in valid context. Program
    Info also populate uniform location as attribute variable

    :param definitionModule: a module that defines shaders' sourcecode
    :param versionStr: "#version 330 core" line without "#version"
    :param tupleOfOrderedPreprocDirectives: Preprocessor-Directives that is going to be prepended before each shader,
                                            without leading #
    """
    # analogue to OGLSuperBible Listing 2.5
    vertShader = glCreateShader( GL_VERTEX_SHADER )
    glShaderSource( vertShader, [ '#version ' + versionStr +'\n'
                                  + _PrependPreProc( definitionModule.__vert__, tupleOfOrderedPreprocDirectives ) ] )
    glCompileShader( vertShader )

    fragShader = glCreateShader( GL_FRAGMENT_SHADER )
    glShaderSource( fragShader, [ '#version ' + versionStr +'\n'
                                  + _PrependPreProc( definitionModule.__frag__, tupleOfOrderedPreprocDirectives ) ] )
    glCompileShader( fragShader )

    if glGetShaderiv( vertShader, GL_COMPILE_STATUS ) != GL_TRUE:
        print( "vert shader error in", definitionModule.__file__ )
        print ( glGetShaderInfoLog( vertShader ).decode('ascii') )

    if glGetShaderiv( fragShader, GL_COMPILE_STATUS ) != GL_TRUE:
        print( "frag shader error in", definitionModule.__file__ )
        print ( glGetShaderInfoLog( fragShader ).decode('ascii') )

    program = glCreateProgram()
    glAttachShader( program, vertShader )
    glAttachShader( program, fragShader )
    glLinkProgram( program )

    if glGetProgramiv( program, GL_LINK_STATUS ) != GL_TRUE:
        print( "prog shader error in", definitionModule.__file__ )
        print ( glGetProgramInfoLog( program ).decode('ascii') )

    glDeleteShader( vertShader )
    glDeleteShader( fragShader )

    # populate uniform location as attribute variable
    progInfo = ProgramInfo( program )
    uniformN = glGetProgramiv( program, GL_ACTIVE_UNIFORMS )

    for uniformIdx in range( uniformN ):
        uniformName = array( 'b', glGetActiveUniformName( program, uniformIdx, 256 ) ).tobytes().decode('ascii')\
                      .rstrip('\0') # trim trailing null-terminators if existed
        setattr( progInfo, uniformName, glGetUniformLocation( program, uniformName ) )

    return progInfo