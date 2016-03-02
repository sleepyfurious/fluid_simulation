from util_glshaderwrangler import *

v = DefineGLSLShaderProgram( GL_VERTEX_SHADER, 'scenebox vert', """
// CONSTANT ------------------------------------------------------------------------------------------------------------
const vec3 BOX_VERTICES[8] = vec3[8](  vec3( 1, 1, 1 ), vec3( 1, 1,-1 ),
                                       vec3(-1, 1, 1 ), vec3(-1, 1,-1 ),
                                       vec3(-1,-1, 1 ), vec3(-1,-1,-1 ),
                                       vec3( 1,-1, 1 ), vec3( 1,-1,-1 )  );

const vec3 BOX_LINEVERTICES[24] = vec3[24](  BOX_VERTICES[0], BOX_VERTICES[1],  BOX_VERTICES[2], BOX_VERTICES[3],
                                             BOX_VERTICES[4], BOX_VERTICES[5],  BOX_VERTICES[6], BOX_VERTICES[7],
                                             BOX_VERTICES[0], BOX_VERTICES[2],  BOX_VERTICES[2], BOX_VERTICES[4],
                                             BOX_VERTICES[4], BOX_VERTICES[6],  BOX_VERTICES[6], BOX_VERTICES[0],
                                             BOX_VERTICES[1], BOX_VERTICES[3],  BOX_VERTICES[3], BOX_VERTICES[5],
                                             BOX_VERTICES[5], BOX_VERTICES[7],  BOX_VERTICES[7], BOX_VERTICES[1] );

// UTIL ----------------------------------------------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------------------------------------------------

uniform mat4 vpMat = mat4( 1 ); // camera

#if/**/ defined(GRID)
    uniform float gridSpacing = 0.1;
    uniform ivec3 gridN = ivec3( 10 );
    uniform sampler2D velocityField;

 #elif  defined(SCENEBOX)
    uniform vec3 boxSize = vec3( 1 );

 #endif

void main ( void ) {
    vec3 wPos;

    #if/**/ defined(GRID)
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

        wPos = gridGroundCenteredCellPos;

     #elif  defined(SCENEBOX)
        wPos = 0.5 *boxSize *BOX_LINEVERTICES[ gl_VertexID ];

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