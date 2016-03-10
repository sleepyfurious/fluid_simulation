from util_glshaderwrangler import *

v = DefineGLSLShaderProgram( GL_VERTEX_SHADER, 'scenebox vert', """
// CONSTANT ------------------------------------------------------------------------------------------------------------
const vec3 BOX_VERTICES[8] = vec3[8](  vec3( 1, 1, 1 ), vec3( 1, 1,-1 ),
                                       vec3(-1, 1, 1 ), vec3(-1, 1,-1 ),
                                       vec3(-1,-1, 1 ), vec3(-1,-1,-1 ),
                                       vec3( 1,-1, 1 ), vec3( 1,-1,-1 )  );

const int BOX_LINEVERTICESIDX[24] = int[24](    0, 1,  2, 3,    4, 5,  6, 7,
                                                0, 2,  2, 4,    4, 6,  6, 0,
                                                1, 3,  3, 5,    5, 7,  7, 1    );

const int BOX_SURFTRIANGLEIDX[ 3 *2 *6 ] = int[ 3 *2 *6 ](  4,6,2, 2,6,0,   6,7,0, 0,7,1,
                                                            7,5,1, 1,5,3,   5,4,3, 3,4,2,
                                                            2,0,3, 3,0,1,   5,7,4, 4,7,6   );

// UTIL ----------------------------------------------------------------------------------------------------------------

ivec3 GetIndex3Dfrom1D( int i, ivec2 wh ) { return  ivec3( i %wh.x, int( i /wh.x ) %wh.y, i /( wh.x *wh.y ) ); }

// ---------------------------------------------------------------------------------------------------------------------

uniform mat4 vpMat = mat4( 1 ); // camera

#if/**/ defined(GRID)
    uniform float cellScale = 0.1;
    uniform float lineScale = 1;
    uniform ivec3 gridN = ivec3( 10 );
    uniform sampler3D velocityField;

 #elif  defined(SCENEBOX)
    uniform vec3 boxSize = vec3( 1 );

 #endif

void main ( void ) {
    vec3 wPos;

    #if/**/ defined(GRID)
        int     cellID = int( gl_VertexID *0.5 );
        bool    isTail  = mod( gl_VertexID, 2 ) == 0.0; // isOdd 0---->1

        vec3    gridSize            = cellScale *gridN;
        vec3    gridCenterPos       = 0.5 *cellScale *( gridN -1 );

        ivec3   cellCoord           = GetIndex3Dfrom1D( cellID, gridN.xy );
        vec3    gridScaledCellPos   = ( gridSize *cellCoord ) / gridN;
        vec3    gridCenteredCellPos = gridScaledCellPos -gridCenterPos;

        if ( isTail ) {
            gridCenteredCellPos += vec3( texelFetch( velocityField, cellCoord, 0 ) ) *lineScale;
        }

        wPos = gridCenteredCellPos;

     #elif  defined(SCENEBOX)
        int boxVertIdx;

        #if/**/ defined(LINE)
            boxVertIdx = BOX_LINEVERTICESIDX[ gl_VertexID ];

         #elif  defined(SURF)
            boxVertIdx = BOX_SURFTRIANGLEIDX[ gl_VertexID ];

         #endif

        wPos = 0.5 *boxSize *BOX_VERTICES[ boxVertIdx ];

     #endif

    gl_Position = vpMat * vec4( wPos, 1 );
}
""" )

########################################################################################################################

f = DefineGLSLShaderProgram( GL_FRAGMENT_SHADER, 'scenebox frag', """
out vec4 color;

void main ( void ) {
    vec3 opaqueCol = vec3( 0.044, 0.687, 0.800 );
    color = vec4( opaqueCol *( 1 -gl_FragCoord.z ), 1.0 );
}
""" )