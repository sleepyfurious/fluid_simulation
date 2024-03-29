from    OpenGL.GL               import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER
from    util_glshaderwrangler   import DefineGLSLShaderProgram

f = DefineGLSLShaderProgram( GL_FRAGMENT_SHADER, 'navierstroke term operation', """
// UTIL ----------------------------------------------------------------------------------------------------------------

vec3 GetNeighborDiff( sampler3D sampler, ivec3 coord ) { return
    vec3( texelFetch( sampler, coord +ivec3(1,0,0), 0 ).x -texelFetch( sampler, coord -ivec3(1,0,0), 0 ).x,
          texelFetch( sampler, coord +ivec3(0,1,0), 0 ).y -texelFetch( sampler, coord -ivec3(0,1,0), 0 ).y,
          texelFetch( sampler, coord +ivec3(0,0,1), 0 ).z -texelFetch( sampler, coord -ivec3(0,0,1), 0 ).z );
}

vec3 GetNeighborAlphaDiff( sampler3D sampler, ivec3 coord ) { return
    vec3( texelFetch( sampler, coord +ivec3(1,0,0), 0 ).a -texelFetch( sampler, coord -ivec3(1,0,0), 0 ).a,
          texelFetch( sampler, coord +ivec3(0,1,0), 0 ).a -texelFetch( sampler, coord -ivec3(0,1,0), 0 ).a,
          texelFetch( sampler, coord +ivec3(0,0,1), 0 ).a -texelFetch( sampler, coord -ivec3(0,0,1), 0 ).a );
}

vec4 GetNeighborSum( sampler3D sampler, ivec3 coord ) { return
    texelFetch( sampler, coord +ivec3(1,0,0), 0 ) +texelFetch( sampler, coord -ivec3(1,0,0), 0 ) +
    texelFetch( sampler, coord +ivec3(0,1,0), 0 ) +texelFetch( sampler, coord -ivec3(0,1,0), 0 ) +
    texelFetch( sampler, coord +ivec3(0,0,1), 0 ) +texelFetch( sampler, coord -ivec3(0,0,1), 0 ); }

// ---------------------------------------------------------------------------------------------------------------------

layout(pixel_center_integer) in vec4 gl_FragCoord;
uniform int  operating_z;

out     vec4 outVar;

#if/**/ defined( ADVECTION )
    uniform sampler3D   u3_1;
    uniform vec3        rGridsize;
    uniform float       dtXrdx;

 #elif  defined( JACOBI )
    uniform sampler3D   fieldX, fieldB;
    uniform vec2        alphaRbeta;

 #elif  defined( FORCE )
    uniform float       rUnitcellspaceHalfBrushsize;
    uniform vec3        unitcellspaceCursorPosition,
                        forceXdt;

 #elif  defined( DIVERGENCE )
    uniform sampler3D   u3_1;
    uniform float       halfRdx;

 #elif  defined( GRADIENTSUB )
    uniform sampler3D   u3_1, _3p1;
    uniform float       halfRdx;

 #elif  defined( BOUNDARY )
    uniform sampler3D   u3p1;
    uniform float       scale;

    #if/**/ defined( BOUNDARY_BORDER )
        flat in ivec3       offset;
     #else
        uniform ivec3       offset;
     #endif

 #endif


 void main ( void ) {
    ivec3 unitcellspaceCoord    = ivec3( gl_FragCoord.xy, operating_z );

#if/**/ defined( ADVECTION )
    vec3 unitcellspaceFromPos   = unitcellspaceCoord -dtXrdx *vec3(texelFetch( u3_1, unitcellspaceCoord, 0 ));
    vec3 texspaceFromPos        = ( unitcellspaceFromPos +0.5 ) *rGridsize;

    outVar = texture( u3_1, texspaceFromPos );

 #elif  defined( FORCE )
    vec3 unitcellspaceCursorVec = unitcellspaceCoord -unitcellspaceCursorPosition;
    float lengthSqUnitcellspaceCursorVec = unitcellspaceCursorVec.x *unitcellspaceCursorVec.x
                                         + unitcellspaceCursorVec.y *unitcellspaceCursorVec.y
                                         + unitcellspaceCursorVec.z *unitcellspaceCursorVec.z;

    outVar.xyz = forceXdt *exp( -lengthSqUnitcellspaceCursorVec *rUnitcellspaceHalfBrushsize );

 #elif  defined( DIVERGENCE )
    vec3 neighborDiffW = GetNeighborDiff( u3_1, unitcellspaceCoord );

    outVar = vec4( halfRdx *( neighborDiffW.x + neighborDiffW.y + neighborDiffW.z ) );

 #elif  defined( JACOBI )
    vec4 x = GetNeighborSum( fieldX, unitcellspaceCoord ), // proj: p
         b = texelFetch( fieldB, unitcellspaceCoord, 0 );  // proj: eq10r

    outVar = ( x +alphaRbeta.x *b ) *alphaRbeta.y;

 #elif  defined( GRADIENTSUB )
    vec3 neighborDiffP = GetNeighborAlphaDiff( _3p1, unitcellspaceCoord );

    outVar.xyz = texelFetch( u3_1, unitcellspaceCoord, 0 ).xyz -halfRdx *neighborDiffP;

 #elif  defined( BOUNDARY )
    outVar = scale *texelFetch( u3p1, unitcellspaceCoord +offset, 0 );
 #endif

 }
""" )

v = DefineGLSLShaderProgram( GL_VERTEX_SHADER, 'navierstroke screen primitive', """
const vec2 QUAD_VERTICES[4] = vec2[4]( vec2( 1, 1 ), vec2(-1, 1 ), vec2(-1,-1 ), vec2( 1,-1 ) );
const int  QUAD_TRIANGLESIDX[ 3 *2 ] = int[ 3 *2 ]( 0, 1, 3,  3, 1, 2 );

#if/**/ defined( BOUNDARY_BORDER )
#define CANVAS_SIZE ivec2( 16, 16 )
    const vec2 _PAD = vec2( -1 +NDCSPACE_PIXELSIZE.x, -1 +NDCSPACE_PIXELSIZE.y );
    const vec2 BORDER_VERTS[ 12 ] = vec2[ 12 ](  vec2(-1-1 ), vec2(-1,1 ), vec2( 1,1 ), vec2( 1,-1),    //  0123
                                                 vec2( _PAD.x,-1 ),          vec2( _PAD.x, 1 ),         //  4  5
                                                 vec2(-_PAD.x,-1 ),          vec2(-_PAD.x, 1 ),         //  6  7
                                                 vec2( _PAD.x, _PAD.y ),     vec2(-_PAD.x, _PAD.y ),    //  8  9
                                                 vec2( _PAD.x,-_PAD.y ),     vec2(-_PAD.x,-_PAD.y )  ); // 10 11

    const int TRIANGLESIDX[ 8 *3 ] = int[ 8 *3 ](   0, 4, 5,  0, 5, 1,      2, 7, 6,  2, 6, 3,
                                                    4, 6, 9,  4, 9, 8,      7, 5,10,  7,10,11    );

    const int OFFSET__VAR[ 4 ] = int[ 4 ]( 1,-1, 0, 0 );
    flat out ivec3 offset;
 #endif

void main ( void ) {
    vec2 vertex;

    #if/**/ defined( BOUNDARY_BORDER )
        int borderSide = int( gl_VertexID *0.1667 );
        offset = ivec3( OFFSET__VAR[ borderSide ], OFFSET__VAR[ ( borderSide +2 ) %4 ], 0 );
        vertex = BORDER_VERTS[ TRIANGLESIDX[ gl_VertexID ] ];

     #else
        vertex = QUAD_VERTICES[ QUAD_TRIANGLESIDX[ gl_VertexID ] ],

     #endif

    gl_Position = vec4( vertex, 0, 1 );
}
""" )