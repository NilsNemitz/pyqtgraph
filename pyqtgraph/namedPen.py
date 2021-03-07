# from ..Qt import QtGui
from .Qt import QtGui, QtCore

from . import functions as fn

__all__ = ['NamedPen']
DEBUG = False

class NamedPen(QtGui.QPen):
    """ Extends QPen to retain a functional color description """
    def __init__(self, name, width=1, alpha=None ):
        """
        Creates a new NamedPen object.
        'name' should be included in 'functions.Colors'
        'width' specifies linewidth and defaults to 1
        'alpha' controls opacity which persists over palette changes
        """
        if DEBUG: print('  NamedBrush created as',name,alpha)
        super().__init__(QtCore.Qt.SolidLine) # Initialize QPen superclass
        super().setWidth(width)
        super().setCosmetic(True)
        self._identifier = (name, alpha)
        self._updateQColor(self._identifier)
        fn.NAMED_COLOR_MANAGER.register( self ) # manually register for callbacks

    def __eq__(self, other): # make this a hashable object
        # return other is self
        if isinstance(other, self.__class__):
            return self._identifier == other._identifier
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return id(self)

    def setColor(self, name=None, alpha=None):
        """ update color name. This does not trigger a global redraw. """
        if name is None:
            name = self._identifier[0]
        elif isinstance(name, QtGui.QColor):
            # this is a workaround for the alpha adjustements in AxisItem:
            # While the color will not change, the alpha value can be adjusted as needed.
            if alpha is None:
                alpha = name.alpha() # extract from given QColor
            name = self._identifier[0]
            if DEBUG: print('  NamedPen: setColor(QColor) call: set alpha to', alpha)
        self._identifier = (name, alpha)
        self._updateQColor(self._identifier)
        
    def setAlpha(self, alpha):
        """ update opacity value """
        self._identifier = (self._identifier[0], alpha)
        self._updateQColor(self._identifier)
        
    def _updateQColor(self, identifier, color_dict=None):
        """ update super-class QColor """
        name, alpha = identifier
        if color_dict is None:
            color_dict = fn.NAMED_COLOR_MANAGER.colors()
        try:
            qcol = fn.Colors[name]
        except ValueError as exc:
            raise ValueError("Color '{:s}' is not in list of defined colors".format(str(name)) ) from exc
        if alpha is not None:
            qcol.setAlpha( alpha )
        if DEBUG: print('  NamedPen updated to QColor ('+str(qcol.name())+')')
        super().setColor( qcol )



    def paletteChange(self, color_dict):
        """ refresh QColor according to lookup of identifier in functions.Colors """
        if DEBUG: print('  NamedPen: style change request:', self, type(color_dict))
        name, alpha = self._identifier
        if color_dict is None: # manually retrieve color manager palette
            color_dict = fn.NAMED_COLOR_MANAGER.colors()
        try:
            qcol = color_dict[name]
            if DEBUG: print('  NamedPen: retrieved new QColor (', qcol.getRgb(), ') for name', name)
        except ValueError as exc:
            raise ValueError("Color {:s} is not in list of defined colors".format(str(name)) ) from exc
        if alpha is not None:
            qcol.setAlpha( alpha )
        super().setColor(qcol)
