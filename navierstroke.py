from glm import *
from sleepy_mockup_glslsampler import *

class Eq12CommonInfo:
    def __init__ ( self, gridspacing: float ):
        self._gridspacing  = gridspacing
        self.lQuantityField2D_1 = None #type: VectorField2D
        self.lQuantityField2D_2 = None #type: VectorField2D
        self.deltaT = float()

    @property
    def gridspacing(self): return self._gridspacing

    @property
    def rGridspacing(self): return 1 /self._gridspacing

    @property
    def halfRGridspacing(self): return 0.5 /self._gridspacing

class Eq12Operator:
    def __init__(self, lEq12CommonInfo: Eq12CommonInfo ): self._lEq12CommonInfo = lEq12CommonInfo
    # return qty4D
    def Execute(self, gridCoord: ivec2)-> vec4: raise NotImplementedError

class Advection ( Eq12Operator ):
    def __init__( self, lEq12CommonInfo: Eq12CommonInfo ): super( Advection, self ).__init__( lEq12CommonInfo )
    def Execute( self, gridCoord: ivec2 )-> vec4:
        u = self._lEq12CommonInfo # uniform variable

        pos = vec2( gridCoord ) -u.deltaT *u.rGridspacing *u.lQuantityField2D_1.GetData( gridCoord ).xy

        # if gridCoord == ivec2( 3, 2 ):
        #     import pdb
        #     pdb.set_trace()

        ret = u.lQuantityField2D_2.GetBiLerp( pos )

        return ret

# Ax = b
class Jacobi ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo ):
        super(Jacobi,self).__init__( lEq12CommonInfo )
        self.alphaRbeta = vec2()

    def Execute ( self, gridCoord: ivec2 )-> vec4:
        u = self._lEq12CommonInfo # uniform variable

        xL = u.lQuantityField2D_1.GetData( gridCoord -ivec2( 1, 0 ) )
        xR = u.lQuantityField2D_1.GetData( gridCoord +ivec2( 1, 0 ) )
        xB = u.lQuantityField2D_1.GetData( gridCoord -ivec2( 0, 1 ) )
        xT = u.lQuantityField2D_1.GetData( gridCoord +ivec2( 0, 1 ) )

        bC = u.lQuantityField2D_2.GetData( gridCoord )

        return  ( xL + xR + xB + xT + self.alphaRbeta.x *bC ) *self.alphaRbeta.y

# this one result in scalar: vec4( scalar )
class Divergence ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo ): super( Divergence, self ).__init__( lEq12CommonInfo )
    def Execute ( self, gridCoord: ivec2 )-> vec4:
        u = self._lEq12CommonInfo # uniform variable

        wL = u.lQuantityField2D_1.GetData( gridCoord -ivec2( 1, 0 ) )
        wR = u.lQuantityField2D_1.GetData( gridCoord +ivec2( 1, 0 ) )
        wB = u.lQuantityField2D_1.GetData( gridCoord -ivec2( 0, 1 ) )
        wT = u.lQuantityField2D_1.GetData( gridCoord +ivec2( 0, 1 ) )

        return vec4( u.halfRGridspacing *( ( wR.x -wL.x ) +( wT.y -wB.y ) ) )

class GradientSubtraction ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo ): super( GradientSubtraction, self ).__init__( lEq12CommonInfo )
    def Execute ( self, gridCoord: ivec2 ) -> vec4:
        u = self._lEq12CommonInfo # uniform variable

        pL = u.lQuantityField2D_1.GetData( gridCoord -ivec2( 1, 0 ) ).x
        pR = u.lQuantityField2D_1.GetData( gridCoord +ivec2( 1, 0 ) ).x
        pB = u.lQuantityField2D_1.GetData( gridCoord -ivec2( 0, 1 ) ).x
        pT = u.lQuantityField2D_1.GetData( gridCoord +ivec2( 0, 1 ) ).x

        ret = u.lQuantityField2D_2.GetData( gridCoord ) #type vec4
        ret.xy -= u.halfRGridspacing *vec2( pR -pL, pT -pB )

        return ret

class Harris2004NavierStrokeSimulation:

    def __init__( self, gridSize: ivec2, gridSpacing: float ):
        self.viscosity = 1.0

        self._gridSize                      = gridSize
        self._velocity2D_field2D            = Vec2DField2D( gridSize )
        self._pressure1nothin1_field2D      = Vec2DField2D( gridSize )
        self._intermediateVal_field2D       = Vec2DField2D( gridSize )
        self._dye1nothin1_field2D           = Vec2DField2D( gridSize )
        self._eq12CommonInfo                = Eq12CommonInfo( gridSpacing )

        self._shader_advection              = Advection( self._eq12CommonInfo )
        self._shader_jacobi                 = Jacobi( self._eq12CommonInfo )
        self._shader_divergence             = Divergence( self._eq12CommonInfo )
        self._shader_gradientSubtraction    = GradientSubtraction( self._eq12CommonInfo )

        self.devTmp_stepCnt = 0

    def Step( self, deltaT: float ):
        dX2         = self._eq12CommonInfo.gridspacing *self._eq12CommonInfo.gridspacing
        dX2_rVdT    = dX2 /( self.viscosity *deltaT )

        # advection
        self._eq12CommonInfo.deltaT = deltaT
        self._eq12CommonInfo.lQuantityField2D_1 = self._velocity2D_field2D
        self._eq12CommonInfo.lQuantityField2D_2 = self._dye1nothin1_field2D
        self.ExecuteShader( self._shader_advection, self._gridSize, self._dye1nothin1_field2D )
        self._eq12CommonInfo.lQuantityField2D_2 = self._velocity2D_field2D
        self.ExecuteShader( self._shader_advection, self._gridSize, self._velocity2D_field2D )

        # viscous diffusion: ok just skip it for now in this rev

        # add force here
        if self.devTmp_stepCnt < 25:
            self.devTmp_stepCnt += 1
            vField = self._velocity2D_field2D
            vField.SetDataVec2( ivec2(0,5), vField.GetData( ivec2(0,5) ).xy +vec2(0.5,0) )
            vField.SetDataVec2( ivec2(5,0), vField.GetData( ivec2(5,0) ).xy +vec2(0,0.5) )

        # compute pressure
        self._eq12CommonInfo.lQuantityField2D_1 = self._velocity2D_field2D
        self.ExecuteShader( self._shader_divergence, self._gridSize, self._intermediateVal_field2D )
        self._eq12CommonInfo.lQuantityField2D_1 = self._pressure1nothin1_field2D
        self._eq12CommonInfo.lQuantityField2D_2 = self._intermediateVal_field2D
        self._shader_jacobi.alphaRbeta = vec2( -dX2, 1 /4 )
        for i in range( 40 ):
            self.ExecuteShader( self._shader_jacobi, self._gridSize, self._pressure1nothin1_field2D )

        # subtract pressure gradient
        self._eq12CommonInfo.lQuantityField2D_2 = self._velocity2D_field2D
        self.ExecuteShader( self._shader_gradientSubtraction, self._gridSize, self._velocity2D_field2D )

    @staticmethod
    def ExecuteShader( shader: Eq12Operator, gridSize: ivec2, targetField: VectorField2D ):
        retField = targetField.CreateNew( targetField.GetFieldSize() ) #type: VectorField2D
        [ retField.SetDataVec4( ivec2(x,y), shader.Execute( ivec2(x,y) ) ) for y in range( gridSize.y ) for x in range( gridSize.x ) ]
        targetField.SwapData( retField )

    def GetACopyOfVelocity2DField2D(self)-> Vec2DField2D: return self._velocity2D_field2D.GetACopy();

    @property
    def gridSize(self)-> ivec2: return ivec2( self._gridSize )

    @property
    def gridSpacing(self)-> float: return self._eq12CommonInfo._gridspacing

