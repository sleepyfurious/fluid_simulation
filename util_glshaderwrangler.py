# I simplify and borrow The Little Grasshopper’s Lua shader wrangler to handle my shader management (a primal one).
# see: http://prideout.net/blog/?p=1
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
# vertShader = DefineGLSLShaderProgram( GL_VERTEX_SHADER, 'hello world vert', """
# void main ( void ) {
# ...
# }
# """ )
#
# fragShader = DefineGLSLShaderProgram( GL_FRAGMENT_SHADER, 'hello world frag', """
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
#  programInfo = BuildPipelineProgram( vertShader, fragShader, ( 'define test', ) )
#
# this is the OpenGl's handle
#  programInfo.__progHandle__
#
# this is the uniform location of the color variable from our example
#  programInfo.color


import inspect
from array import array
from OpenGL.GL import *

def DefineGLSLShaderProgram( stage, wranglerName, sourcecode )-> str:
    callerFrameInfo = inspect.getouterframes( inspect.currentframe() )[1] #type: inspect.FrameInfo
    sourcecodelineN = sourcecode.count('\n') +1

    return '//' +wranglerName \
           + '\n#line ' +str( callerFrameInfo.lineno -sourcecodelineN +2 ) +sourcecode

class ProgramInfo:
    def __init__( self, progHandle ):
        self.__progHandle__ = progHandle

def _PrependPreProc( shaderSource, tupleOfOrderedPreprocDirectives ):
    prependedStr = ''.join( [ '#define ' + item +'\n' for item in tupleOfOrderedPreprocDirectives ] )
    return prependedStr +shaderSource

versionStr = '330 core'

def BuildPipelineProgram(
    vertShaderDefinitionStr: str, fragShaderDefinitionStr: str, tupleOfOrderedPreprocDirectives
)-> ProgramInfo:
    """build OpenGL Program Pipeline in current GL context.

    Return ProgramInfo that contain attribute progHandle that is GL's handle. beware to build in valid context. Program
    Info also populate uniform location as attribute variable

    :param vertShaderDefinitionStr: a string that defines vertex shaders' sourcecode
    :param fragShaderDefinitionStr: a string that defines fragment shaders' sourcecode
    :param versionStr: "#version 330 core" line without "#version"
    :param tupleOfOrderedPreprocDirectives: Preprocessor-Directives that is going to be prepended before each shader,
                                            without leading #
    """
    # analogue to OGLSuperBible Listing 2.5
    vertShader = glCreateShader( GL_VERTEX_SHADER )
    glShaderSource( vertShader, [ '#version ' + versionStr +'\n'
                                  + _PrependPreProc( vertShaderDefinitionStr, tupleOfOrderedPreprocDirectives ) ] )
    glCompileShader( vertShader )

    fragShader = glCreateShader( GL_FRAGMENT_SHADER )
    glShaderSource( fragShader, [ '#version ' + versionStr +'\n'
                                  + _PrependPreProc( fragShaderDefinitionStr, tupleOfOrderedPreprocDirectives ) ] )
    glCompileShader( fragShader )

    if glGetShaderiv( vertShader, GL_COMPILE_STATUS ) != GL_TRUE:
        print( "vert shader error in", vertShaderDefinitionStr.splitlines()[0] )
        print ( glGetShaderInfoLog( vertShader ).decode('ascii') )

    if glGetShaderiv( fragShader, GL_COMPILE_STATUS ) != GL_TRUE:
        print( "frag shader error in", fragShaderDefinitionStr.splitlines()[0] )
        print ( glGetShaderInfoLog( fragShader ).decode('ascii') )

    program = glCreateProgram()
    glAttachShader( program, vertShader )
    glAttachShader( program, fragShader )
    glLinkProgram( program )

    glDeleteShader( vertShader )
    glDeleteShader( fragShader )

    # clean up and raise if there is a problem
    if glGetProgramiv( program, GL_LINK_STATUS ) != GL_TRUE:
        print( "prog shader error in", vertShaderDefinitionStr.splitlines()[0] +"-" +fragShaderDefinitionStr.splitlines()[0] )
        print ( glGetProgramInfoLog( program ).decode('ascii') )

        glDeleteProgram( program )
        raise Exception

    # populate uniform location as attribute variable
    progInfo = ProgramInfo( program )
    uniformN = glGetProgramiv( program, GL_ACTIVE_UNIFORMS )

    for uniformIdx in range( uniformN ):
        uniformName = array( 'b', glGetActiveUniformName( program, uniformIdx, 256 ) ).tobytes().decode('ascii') \
            .rstrip('\0') # trim trailing null-terminators if existed
        setattr( progInfo, uniformName, glGetUniformLocation( program, uniformName ) )

    return progInfo