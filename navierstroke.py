from glm import *
from sleepy_mockup_glslsampler import *
from looptimer import *

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
        u = self._lEq12CommonInfo # uniform block variable

        pos = vec2( gridCoord ) -u.deltaT *u.rGridspacing *u.lQuantityField2D_1.GetData( gridCoord ).xy

        return u.lQuantityField2D_2.GetBiLerp( pos )

# Ax = b
class Jacobi ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo ):
        super(Jacobi,self).__init__( lEq12CommonInfo )
        self.alphaRbeta = vec2()

    def Execute ( self, gridCoord: ivec2 )-> vec4:
        u = self._lEq12CommonInfo # uniform block variable

        xL, xR, xB, xT = u.lQuantityField2D_1.GetDataLRBT( gridCoord )

        bC = u.lQuantityField2D_2.GetData( gridCoord )

        return  ( xL + xR + xB + xT + self.alphaRbeta.x *bC ) *self.alphaRbeta.y

# this one result in scalar: vec4( scalar )
class Divergence ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo ): super( Divergence, self ).__init__( lEq12CommonInfo )
    def Execute ( self, gridCoord: ivec2 )-> vec4:
        u = self._lEq12CommonInfo # uniform block variable

        wL, wR, wB, wT = u.lQuantityField2D_1.GetDataLRBT( gridCoord )

        return vec4( u.halfRGridspacing *( ( wR.x -wL.x ) +( wT.y -wB.y ) ) )

class GradientSubtraction ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo ): super( GradientSubtraction, self ).__init__( lEq12CommonInfo )
    def Execute ( self, gridCoord: ivec2 ) -> vec4:
        u = self._lEq12CommonInfo # uniform block variable

        pL, pR, pB, pT = u.lQuantityField2D_1.GetDataLRBT( gridCoord )

        ret = u.lQuantityField2D_2.GetData( gridCoord ) #type vec4
        ret.xy -= u.halfRGridspacing *vec2( pR.x -pL.x, pT.x -pB.x )

        return ret

class Boundary ( Eq12Operator ):
    def __init__ ( self, lEq12CommonInfo: Eq12CommonInfo  ):
        super( Boundary, self ).__init__( lEq12CommonInfo )
        self.offset = None #type: ivec2
        self.scale  = None #type: float

    def Execute( self, gridCoord: ivec2 ) -> vec4:
        u = self._lEq12CommonInfo # uniform block variable
        return self.scale * u.lQuantityField2D_1.GetData( gridCoord +self.offset )

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
        self._shader_boundary               = Boundary( self._eq12CommonInfo )

        self.devTmp_stepCnt = 0
        # self._outerLoopTimer = LoopTimer()

    def Step( self, deltaT: float ):
        # print( "OUTER LOOP", self._outerLoopTimer.GetElapsedInSecond() )
        # loopTimer = LoopTimer()
        # operationTimer = LoopTimer()

        dX2         = self._eq12CommonInfo.gridspacing *self._eq12CommonInfo.gridspacing
        dX2_rVdT    = dX2 /( self.viscosity *deltaT )
        # print( "CONSTANT:", operationTimer.GetElapsedInSecond() )

        # advection
        self._eq12CommonInfo.deltaT = deltaT
        self._eq12CommonInfo.lQuantityField2D_1 = self._velocity2D_field2D
        self._eq12CommonInfo.lQuantityField2D_2 = self._dye1nothin1_field2D
        self.ExecuteShaderToInteriorFragments( self._shader_advection, self._gridSize, self._dye1nothin1_field2D )
        self._eq12CommonInfo.lQuantityField2D_2 = self._velocity2D_field2D
        self.ExecuteShaderToInteriorFragments( self._shader_advection, self._gridSize, self._velocity2D_field2D )
        # print( "ADVECTION:", operationTimer.GetElapsedInSecond() )

        # velocity boundary condition
        self._eq12CommonInfo.lQuantityField2D_1 = self._velocity2D_field2D
        self._shader_boundary.scale  = -1.0
        self._shader_boundary.offset = ivec2( 1, 0 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 0, 0, 1, self.gridSize.y ), self._velocity2D_field2D )
        self._shader_boundary.offset = ivec2( -1, 0 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( self.gridSize.x -1, 0, 1, self.gridSize.y ), self._velocity2D_field2D )
        self._shader_boundary.offset = ivec2( 0, 1 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 1, 0, self.gridSize.x -2, 1 ), self._velocity2D_field2D )
        self._shader_boundary.offset = ivec2( 0, -1 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 1, self.gridSize.y -1, self.gridSize.x -2, 1 ), self._velocity2D_field2D )
        # print( "ADVECTION BOUNDARY:", operationTimer.GetElapsedInSecond() )

        # viscous diffusion: ok just skip it for now in this rev

        # add force here
        if self.devTmp_stepCnt < 100 and self.devTmp_stepCnt > 1:
            vField = self._velocity2D_field2D
            vField.SetDataVec2( ivec2(1,5), vField.GetData( ivec2(1,5) ).xy +vec2(20,0) *deltaT )
            vField.SetDataVec2( ivec2(5,1), vField.GetData( ivec2(5,1) ).xy +vec2(0,20) *deltaT )
        # print( "FORCE:", operationTimer.GetElapsedInSecond() )

        # compute pressure
        self._eq12CommonInfo.lQuantityField2D_1 = self._velocity2D_field2D
        self.ExecuteShaderToFragments( self._shader_divergence, self._gridSize, self._intermediateVal_field2D )
        self._eq12CommonInfo.lQuantityField2D_1 = self._pressure1nothin1_field2D
        self._eq12CommonInfo.lQuantityField2D_2 = self._intermediateVal_field2D
        self._shader_jacobi.alphaRbeta = vec2( -dX2, 1 /4 )
        for i in range( 1 ):
            self.ExecuteShaderToInteriorFragments( self._shader_jacobi, self._gridSize, self._pressure1nothin1_field2D )
            # pressure boundary condition
            self._shader_boundary.scale = 1.0
            self._eq12CommonInfo.lQuantityField2D_1 = self._pressure1nothin1_field2D
            self._shader_boundary.offset = ivec2( 1, 0 )
            self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 0, 0, 1, self.gridSize.y ), self._pressure1nothin1_field2D )
            self._shader_boundary.offset = ivec2( -1, 0 )
            self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( self.gridSize.x -1, 0, 1, self.gridSize.y ), self._pressure1nothin1_field2D )
            self._shader_boundary.offset = ivec2( 0, 1 )
            self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 1, 0, self.gridSize.x -2, 1 ), self._pressure1nothin1_field2D )
            self._shader_boundary.offset = ivec2( 0, -1 )
            self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 1, self.gridSize.y -1, self.gridSize.x -2, 1 ), self._pressure1nothin1_field2D )
        # print( "PRESSURE WITH BOUNDARY:", operationTimer.GetElapsedInSecond() )

        # subtract pressure gradient
        self._eq12CommonInfo.lQuantityField2D_1 = self._pressure1nothin1_field2D
        self._eq12CommonInfo.lQuantityField2D_2 = self._velocity2D_field2D
        self.ExecuteShaderToInteriorFragments( self._shader_gradientSubtraction, self._gridSize, self._velocity2D_field2D )
        # print( "SUBTRACT PRESSURE GRADIENT:", operationTimer.GetElapsedInSecond() )

        # velocity boundary condition
        self._eq12CommonInfo.lQuantityField2D_1 = self._velocity2D_field2D
        self._shader_boundary.scale  = -1.0
        self._shader_boundary.offset = ivec2( 1, 0 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 0, 0, 1, self.gridSize.y ), self._velocity2D_field2D )
        self._shader_boundary.offset = ivec2( -1, 0 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( self.gridSize.x -1, 0, 1, self.gridSize.y ), self._velocity2D_field2D )
        self._shader_boundary.offset = ivec2( 0, 1 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 1, 0, self.gridSize.x -2, 1 ), self._velocity2D_field2D )
        self._shader_boundary.offset = ivec2( 0, -1 )
        self.ExecuteShaderInplaceToFragments( self._shader_boundary, ivec4( 1, self.gridSize.y -1, self.gridSize.x -2, 1 ), self._velocity2D_field2D )
        # print( "FINAL ADVECTION BOUNDARY:", operationTimer.GetElapsedInSecond() )

        # print( "WHOLE LOOP", loopTimer.GetElapsedInSecond() )
        # self._outerLoopTimer = LoopTimer()
        self.devTmp_stepCnt += 1

    @staticmethod
    def ExecuteShaderInplaceToFragments(
        shader: Eq12Operator, boundaryOfExecutionXYWH: ivec4, targetField: VectorField2D
    ):
        [
            targetField.SetDataVec4( ivec2( x, y ), shader.Execute( ivec2( x, y ) ) )
            for y in range( boundaryOfExecutionXYWH.y, boundaryOfExecutionXYWH.y +boundaryOfExecutionXYWH.w )
            for x in range( boundaryOfExecutionXYWH.x, boundaryOfExecutionXYWH.x +boundaryOfExecutionXYWH.z)
        ]

    @staticmethod
    def ExecuteShaderToFragments( shader: Eq12Operator, gridSize: ivec2, targetField: VectorField2D ):
        retField = targetField.CreateNew( targetField.GetFieldSize() ) #type: VectorField2D
        [   # interior execution
            retField.SetDataVec4( ivec2(x,y), shader.Execute( ivec2(x,y) ) )
            for y in range( 0, gridSize.y ) for x in range( 0, gridSize.x )
        ]

        targetField.SwapData( retField )

    @staticmethod
    def ExecuteShaderToInteriorFragments( shader: Eq12Operator, gridSize: ivec2, targetField: VectorField2D ):
        retField = targetField.CreateNew( targetField.GetFieldSize() ) #type: VectorField2D
        [   # interior execution
            retField.SetDataVec4( ivec2(x,y), shader.Execute( ivec2(x,y) ) )
            for y in range( 1, gridSize.y -1 ) for x in range( 1, gridSize.x -1 )
        ]
        [   # boundary execution: just copy
            retField.SetDataVec4( ivec2( 0, y ), targetField.GetData( ivec2( 0, y ) ) )
            for y in range( 0, gridSize.y )
        ]
        [   # boundary execution: just copy
            retField.SetDataVec4( ivec2( gridSize.x -1, y ), targetField.GetData( ivec2( gridSize.x -1, y ) ) )
            for y in range( 0, gridSize.y )
        ]
        [   # boundary execution: just copy
            retField.SetDataVec4( ivec2( x, 0 ), targetField.GetData( ivec2( x, 0 ) ) )
            for x in range( 1, gridSize.x -1 )
        ]
        [   # boundary execution: just copy
            retField.SetDataVec4( ivec2( x, gridSize.y -1 ), targetField.GetData( ivec2( x, gridSize.y -1 ) ) )
            for x in range( 1, gridSize.x -1 )
        ]

        targetField.SwapData( retField )

    def GetACopyOfVelocity2DField2D(self)-> Vec2DField2D: return self._velocity2D_field2D.GetACopy();

    @property
    def gridSize(self)-> ivec2: return ivec2( self._gridSize )

    @property
    def gridSpacing(self)-> float: return self._eq12CommonInfo._gridspacing

