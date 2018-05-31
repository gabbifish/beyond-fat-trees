from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class ECMP( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=custom_controller.log,w openflow.of_01 --port=%s ext.custom_controller --routing=ECMP' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
class HYB( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=custom_controller.log,w openflow.of_01 --port=%s ext.custom_controller --routing=HYB' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
controllers={ 'hyb': HYB, 'ecmp': ECMP }
