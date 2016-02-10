import time

""" a Timer that restart counting when Init and GetElapsedSecond """
class LoopTimer:
    def __init__( self ):
        self.prev = time.time() # seconds since the epoch as a floating point

    def GetElapsedInSecond ( self ):
        _prev       = self.prev
        self.prev   = time.time()   # now
        return self.prev - _prev