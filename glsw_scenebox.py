from glsl_wrangler import *

DefineGLSLShaderProgram( GL_VERTEX_SHADER, """
uniform mat4 vpMat = mat4( 1 );
uniform vec3 boxSize = vec3( 1 );

void main ( void ) {
    vec3 boxVertices[8] = vec3[8](  vec3( 1, 1, 1 ), vec3( 1, 1,-1 ),
                                    vec3(-1, 1, 1 ), vec3(-1, 1,-1 ),
                                    vec3(-1,-1, 1 ), vec3(-1,-1,-1 ),
                                    vec3( 1,-1, 1 ), vec3( 1,-1,-1 )  );
    vec3 boxLineVertices[24] = vec3[24](
        boxVertices[0], boxVertices[1],  boxVertices[2], boxVertices[3],
        boxVertices[4], boxVertices[5],  boxVertices[6], boxVertices[7],
        boxVertices[0], boxVertices[2],  boxVertices[2], boxVertices[4],
        boxVertices[4], boxVertices[6],  boxVertices[6], boxVertices[0],
        boxVertices[1], boxVertices[3],  boxVertices[3], boxVertices[5],
        boxVertices[5], boxVertices[7],  boxVertices[7], boxVertices[1]
    );

    gl_Position = vpMat * vec4( 0.5 *boxSize *boxLineVertices[ gl_VertexID ], 1 );
}
""" )

DefineGLSLShaderProgram( GL_FRAGMENT_SHADER, """
out vec4 color;

void main ( void ) {
    vec3 opaqueCol = vec3( 0.044, 0.687, 0.800 );
    color = vec4( opaqueCol *( 1 -gl_FragCoord.z ), 1.0 );
}
""" )