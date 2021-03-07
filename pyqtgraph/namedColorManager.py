# from .Qt import QtGui, QtCore, QT_LIB, QtVersion
from .Qt import QtCore, QtGui

import weakref

__all__ = ['NamedColorManager']
DEBUG = True

DEFAULT_COLORS = {
    'b': QtGui.QColor(  0,  0,255,255),
    'g': QtGui.QColor(  0,255,  0,255),
    'r': QtGui.QColor(255,  0,  0,255),
    'c': QtGui.QColor(  0,255,255,255),
    'm': QtGui.QColor(255,  0,255,255),
    'y': QtGui.QColor(255,255,  0,255),
    'k': QtGui.QColor(  0,  0,  0,255),
    'w': QtGui.QColor(255,255,255,255),
    'd': QtGui.QColor(150,150,150,255),
    'l': QtGui.QColor(200,200,200,255),
    's': QtGui.QColor(100,100,150,255),
    'gr_acc':QtGui.QColor(200,200,100,255), # graphical accent color: pastel yellow 
    'gr_reg':QtGui.QColor(  0,  0,255, 50)  # graphical region marker: translucent blue
}
for key, col in [ # add functional colors
    ('gr_fg','d'),  # graphical foreground
    ('gr_bg','k'),  # graphical background
    ('gr_txt','d'), # graphical text color
    ('gr_hov','r')  # graphical hover color
]:
    DEFAULT_COLORS[key] = DEFAULT_COLORS[col]

for idx, col in enumerate( ( # twelve predefined plot colors
    'l','y','r','m','b','c','g','d','d','d','d','d'
) ): 
    key = 'p{:X}'.format(idx)
    DEFAULT_COLORS[key] = DEFAULT_COLORS[col]

# define and instantiate a SignalSource object to pass signals to all pyqtgraph elements
class NamedColorManager(QtCore.QObject): # this needs to emit QEvents
    """
    Singleton QObject that provides palette change signals
    Instantiated by 'functions.py' and retrievable as functions.NAMED_COLOR_MANAGER
    """
    try: # generic name used by pyside:
        paletteChangeSignal = QtCore.Signal(dict)
        paletteHasChangedSignal = QtCore.Signal()
    except AttributeError: # fall back to the PyQt naming scheme
        paletteChangeSignal = QtCore.pyqtSignal(dict)
        paletteHasChangedSignal = QtCore.pyqtSignal()

    def __init__(self, color_dic):
        """ initialization """
        super().__init__()
        self.color_dic = color_dic # this is the imported functions.Colors!
        self.color_dic.clear()
        self.color_dic.update( DEFAULT_COLORS)
        # QPen and others are not QObjects and cannot react to signals:
        self.registered_objects = weakref.WeakSet() # set of objects that request paletteChange callbacks

    def colors(self):
        """ return current list of colors """
        return self.color_dic # it would be safer (but slower) to provide only a copy
    
    def register(self, obj):
        """ register a function for paletteChange callback """
        self.registered_objects.add( obj )

    def redefinePalette(self, color_dic):
        """ update list of named colors, emitsignals to color objects and widgets """
        if color_dic is not None:
            # self.color_dic.clear()
            # self.color_dic.update( DEFAULT_COLORS)
            for key in DEFAULT_COLORS:
                if key not in color_dic:
                    raise ValueError("Palette definition is missing '"+str(key)+"'")
        if DEBUG: print('  NCM: confirmed all color definitions are present, setting palette')
        self.color_dic.clear()
        self.color_dic.update(color_dic)

        # notifies named color objects of new assignments:
        for obj in self.registered_objects:
            obj.paletteChange( self.color_dic )

        # notify all graphics widgets that redraw is required:
        self.paletteHasChangedSignal.emit()
