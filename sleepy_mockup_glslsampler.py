from glm import *
from math import *

class VectorField2D:
    def __init__( self, size: ivec2 ):
        self._data = self.CreateBlankData( size )
        self._fieldSizeMax = size -1

    @staticmethod
    def CreateBlankData( size: ivec2 )-> list: raise NotImplementedError
    def CreateNew( self, size: ivec2 )-> 'derived class': raise NotImplementedError
    def GetACopy( self )-> 'derived class':
        fieldSize = self.GetFieldSize()
        ret = self.CreateNew( fieldSize )
        for y in range( fieldSize.y ):
            for x in range( fieldSize.x ):
                ret._data[ y ][ x ] = self._data[ y ][ x ]

        return ret
    def SwapData( self, other: 'VectorField2D' ):
        temp = self._data
        self._data = other._data
        other._data = temp

    def GetData( self, gridCoord: ivec2 )-> vec4: raise NotImplementedError
    def GetDataLRBT( self, gridCoord: ivec2 ) -> 'tuple of vec4 LRBT': raise NotImplementedError
    def SetDataVec2( self, gridCoord: ivec2, v: vec2 ): raise NotImplementedError
    def SetDataVec4( self, gridCoord: ivec2, v: vec4 ): raise NotImplementedError

    def GetFieldSize( self )-> ivec2: return self._fieldSizeMax +1

    def GetWrapInCoord( self, gridCoord: ivec2 )-> ivec2:
        max = self._fieldSizeMax
        x, y = list( gridCoord )
        if x < 0: x = 0
        if y < 0: y = 0
        if x > max.x: x = max.x
        if y > max.y: y = max.y
        return ivec2( x, y )

    def GetBiLerp( self, gridCoord: vec2 )-> vec4:
        # https://en.wikipedia.org/wiki/Bilinear_interpolation > Algorithm
        x1 = floor( gridCoord.x )
        x2 = ceil( gridCoord.x )
        y1 = floor( gridCoord.y )
        y2 = ceil( gridCoord.y )

        fX_Y1 = ( x2 -gridCoord.x ) *self.GetData( ivec2( x1, y1 ) ) \
              + ( gridCoord.x -x1 ) *self.GetData( ivec2( x2, y1 ) )
        fX_Y2 = ( x2 -gridCoord.x ) *self.GetData( ivec2( x1, y2 ) ) \
              + ( gridCoord.x -x1 ) *self.GetData( ivec2( x2, y2 ) )

        return ( y2 -gridCoord.y ) *fX_Y1 + ( gridCoord.y - y1 ) *fX_Y2 # fXY

class Vec2DField2D ( VectorField2D ):
    def __init__ ( self, size: ivec2 ): super( Vec2DField2D, self ).__init__( size )

    @staticmethod
    def CreateBlankData( size: ivec2 )-> list:
        return [ [ vec2() for x in range( size.x ) ] for y in range( size.y ) ]

    def CreateNew( self, size: ivec2 )-> 'Vec2DField2D': return Vec2DField2D( size )

    def SetDataVec2 ( self, gridCoord: ivec2, v: vec2 ): self._data[ gridCoord.y ][ gridCoord.x ] = vec2( v )
    def SetDataVec4 ( self, gridCoord: ivec2, v: vec4 ): self._data[ gridCoord.y ][ gridCoord.x ] = vec2( v.xy )
    def GetData ( self, gridCoord: ivec2 ) -> vec4:
        _gridCoord = self.GetWrapInCoord( gridCoord )
        return vec4( self._data[ _gridCoord.y ][ _gridCoord.x ] )
    def GetDataLRBT( self, gridCoord: ivec2 ) -> 'tuple of vec4 LRBT':
        l = self.GetWrapInCoord( gridCoord -1 )
        m = self.GetWrapInCoord( gridCoord +1 )
        return ( vec4( self._data[ gridCoord.y ][ l.x ] ), vec4( self._data[ gridCoord.y ][ m.x ] ),
                 vec4( self._data[ l.y ][ gridCoord.x ] ), vec4( self._data[ m.y ][ gridCoord.x ] ) )
    def GetRawData ( self )-> list: # list of concatinated float
        return [ valueElement for rowY in self._data for itemX in rowY for valueElement in itemX ]


class Vec4DField2D ( VectorField2D ):
    def __init__ ( self, size: ivec2 ): super( Vec4DField2D, self ).__init__( size )

    @staticmethod
    def CreateBlankData( size: ivec2 )-> list:
        return [ [ vec4() for x in range( size.x ) ] for y in range( size.y ) ]

    def CreateNew( self, size: ivec2 )-> 'Vec4DField2D': return Vec4DField2D( size )

    def SetDataVec2 ( self, gridCoord: ivec2, v: vec2 ): self._data[ gridCoord.y ][ gridCoord.x ] = vec4( v )
    def SetDataVec4 ( self, gridCoord: ivec2, v: vec4 ): self._data[ gridCoord.y ][ gridCoord.x ] = v
    def GetData ( self, gridCoord: ivec2 ) -> vec4:
        _gridCoord = self.GetWrapInCoord( gridCoord )
        return self._data[ _gridCoord.y ][ _gridCoord.x ]
    def GetDataLRBT( self, gridCoord: ivec2 ) -> 'tuple of vec4 LRBT':
        l = self.GetWrapInCoord( gridCoord -1 )
        m = self.GetWrapInCoord( gridCoord +1 )
        return ( self._data[ gridCoord.y ][ l.x ], self._data[ gridCoord.y ][ m.x ],
                 self._data[ l.y ][ gridCoord.x ], self._data[ m.y ][ gridCoord.x ] )
