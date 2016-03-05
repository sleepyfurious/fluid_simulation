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
    uniform float       dtXrGridspacing;

 #elif  defined( JACOBI )
    uniform sampler3D   fieldX, fieldB;
    uniform vec2        alphaRbeta;

 #elif  defined( FORCE )
    uniform float       rUnitcellspaceHalfBrushsize;
    uniform vec3        unitcellspaceCursorPosition,
                        forceXdt;

 #elif  defined( DIVERGENCE )
    uniform sampler3D   u3_1;
    uniform float       halfRgridspacing;

 #elif  defined( GRADIENTSUB )
    uniform sampler3D   u3_1, _3p1;
    uniform float       halfRgridspacing;

 #endif

 void main ( void ) {
    ivec3 unitcellspaceCoord    = ivec3( gl_FragCoord.xy, operating_z );

#if/**/ defined( ADVECTION )
    vec3 unitcellspaceFromPos   = unitcellspaceCoord -dtXrGridspacing *vec3(texelFetch( u3_1, unitcellspaceCoord, 0 ));
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

    outVar = vec4( halfRgridspacing *( neighborDiffW.x + neighborDiffW.y + neighborDiffW.z ) );

 #elif  defined( JACOBI )
    vec4 x = GetNeighborSum( fieldX, unitcellspaceCoord ),
         b = texelFetch( fieldB, unitcellspaceCoord, 0 );

    outVar = ( x +alphaRbeta.x *b ) *alphaRbeta.y;

 #elif  defined( GRADIENTSUB )
    vec3 neighborDiffP = GetNeighborAlphaDiff( _3p1, unitcellspaceCoord );

    outVar.xyz = texelFetch( u3_1, unitcellspaceCoord, 0 ).xyz -halfRgridspacing *neighborDiffP;
 #endif

 }
""" )

v = DefineGLSLShaderProgram( GL_VERTEX_SHADER, 'navierstroke scr quad', """
const vec2 QUAD_VERTICES[4] = vec2[4]( vec2( 1, 1 ), vec2(-1, 1 ), vec2(-1,-1 ), vec2( 1,-1 ) );
const int  QUAD_TRIANGLESIDX[ 3 *2 ] = int[ 3 *2 ]( 0, 1, 3,  3, 1, 2 );

void main ( void ) {
    gl_Position = vec4( QUAD_VERTICES[ QUAD_TRIANGLESIDX[ gl_VertexID ] ], 0, 1 );
}
""" )
