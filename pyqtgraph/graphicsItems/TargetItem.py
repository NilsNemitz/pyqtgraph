from math import atan2, pi

from ..Qt import QtGui, QtCore
from ..Point import Point
from .. import functions as fn
from .GraphicsObject import GraphicsObject
from .UIGraphicsItem import UIGraphicsItem
from .TextItem import TextItem


def makeTarget(radii=(5, 10, 10)) -> QtGui.QPainterPath:
    path = QtGui.QPainterPath()
    r, w, h = radii
    rect = QtCore.QRectF(-r, -r, r * 2, r * 2)
    path.addEllipse(rect)
    path.moveTo(-w, 0)
    path.lineTo(w, 0)
    path.moveTo(0, -h)
    path.lineTo(0, h)
    return path


class TargetItem(UIGraphicsItem):
    """Draws a draggable target symbol (circle plus crosshair).

    The size of TargetItem will remain fixed on screen even as the view is zoomed.
    Includes an optional text label.
    """

    sigPositionChanged = QtCore.Signal(object)
    sigPositionChangeFinished = QtCore.Signal(object)

    def __init__(
        self,
        pos=None,
        movable=True,
        pen=None,
        hoverPen=None,
        brush=None,
        hoverBrush=None,
        path=None,
        label=None,
        labelOpts=None,
    ):
        """
        Parameters
        ----------
        pos : list, tuple, QPointF, or QPoint
            Initial position of the cursor.
        radius : int
            Size of the cursor in pixels
        cursor : str
            String that defines the shape of the cursor (can take the following
            values for the moment : 's' (square), 'c' (circle))
        pen : QPen, tuple, list or str
            Pen to use when drawing line. Can be any arguments that are valid
            for :func:`~pyqtgraph.mkPen`. Default pen is transparent yellow.
        brush : QBrush, tuple, list, or str
            Defines the brush that fill the cursor. Can be any arguments that
            is valid for :func:`~pyqtgraph.mkBrush`. Default is transparent
            blue.
        movable : bool
            If True, the cursor can be dragged to a new position by the user.
        hoverPen : QPen, tuple, list, or str
            Pen to use when drawing cursor when hovering over it. Can be any
            arguments that are valid for :func:`~pyqtgraph.mkPen`. Default pen
            is red.
        hoverBrush : QBrush, tuple, list or str
            Brush to use to fill the cursor when hovering over it. Can be any
            arguments that is valid for :func:`~pyqtgraph.mkBrush`. Default is
            transparent blue.
        label : str or callable, optional
            Text to be displayed in a label attached to the cursor, or None to
            show no label (default is None). May optionally include formatting
            strings to display the cursor value, or a callable that accepts x
            and y as inputs.
        labelOpts : dict
            A dict of keyword arguments to use when constructing the text
            label. See :class:`CursorLabel` and :class: `~pyqtgraph.TextItem`.
        """
        super().__init__(self)
        self._bounds = None
        self.movable = movable
        self.moving = False
        self.label = None
        self.labelAngle = 0

        self.mouseHovering = False

        if pen is None:
            pen = (255, 255, 0)
        self.setPen(pen)

        if hoverPen is None:
            hoverPen = (255, 0, 255)
        self.setHoverPen(hoverPen)

        if brush is None:
            brush = (0, 0, 255, 50)
        self.setBrush(brush)

        if hoverBrush is None:
            hoverBrush = (0, 255, 255, 100)
        self.setHoverBrush(hoverBrush)

        self.currentPen = self.pen
        self.currentBrush = self.brush

        self._shape = None

        self._pos = (0, 0)
        if pos is None:
            pos = (0, 0)
        self.setPos(pos)

        self._path = None
        if path is None:
            path = makeTarget()
        self.setPath(path)

        self.setLabel(label, labelOpts)

    def setPos(self, pos):
        if isinstance(pos, tuple):
            newPos = pos
        elif isinstance(pos, list):
            newPos = tuple(pos)
        elif isinstance(pos, (QtCore.QPointF, QtCore.QPoint)):
            newPos = (pos.x(), pos.y())
        else:
            raise TypeError
        if self._pos != newPos:
            self._pos = newPos
            super().setPos(Point(self._pos))
            self.sigPositionChanged.emit(self)

    def setBrush(self, *args, **kwargs):
        """Set the brush that fills the cursor. Allowable arguments are any that
        are valid for :func:`~pyqtgraph.mkBrush`.
        """
        self.brush = fn.mkBrush(*args, **kwargs)
        if not self.mouseHovering:
            self.currentBrush = self.brush
            self.update()

    def setHoverBrush(self, *args, **kwargs):
        """Set the brush that fills the cursor when hovering over it. Allowable
        arguments are any that are valid for :func:`~pyqtgraph.mkBrush`.
        """
        self.hoverBrush = fn.mkBrush(*args, **kwargs)
        if self.mouseHovering:
            self.currentBrush = self.hoverBrush
            self.update()

    def setPen(self, *args, **kwargs):
        """Set the pen for drawing the cursor. Allowable arguments are any that
        are valid for :func:`~pyqtgraph.mkPen`."""
        self.pen = fn.mkPen(*args, **kwargs)
        if not self.mouseHovering:
            self.currentPen = self.pen
            self.update()

    def setHoverPen(self, *args, **kwargs):
        """Set the pen for drawing the cursor when hovering over it. Allowable
        arguments are any that are valid for
        :func:`~pyqtgraph.mkPen`."""
        self.hoverPen = fn.mkPen(*args, **kwargs)
        if self.mouseHovering:
            self.currentPen = self.hoverPen
            self.update()

    def setLabel(self, label=None, labelOpts=None):
        if label is None and self.label is not None:
            # remove the label if it's already added
            self.label.scene().removeItem(self.label)
            self.label = None
        else:
            if self.label is None:
                # add a label
                labelOpts = {} if labelOpts is None else labelOpts
                self.label = TargetLabel(self, **labelOpts)
            else:
                # update the label text
                self.label.setText(label)
            self._updateLabel()

    def setLabelAngle(self, angle):
        if self.label is None:
            return
        if self.label.angle != angle:
            self.label.angle = angle
            self._updateLabel()

    def boundingRect(self):
        return self.shape().boundingRect()

    def paint(self, p, *_):
        p.setPen(self.currentPen)
        p.setBrush(self.currentBrush)
        p.drawPath(self.shape())

    def setPath(self, path):
        if path != self._path:
            self._path = path
            self._shape = None
        return None

    def shape(self):
        if self._shape is None:
            s = self.generateShape()
            if s is None:
                return self._path
            self._shape = s
            # beware--this can cause the view to adjust
            # which would immediately invalidate the shape.
            self.prepareGeometryChange()
        return self._shape

    def generateShape(self):
        dt = self.deviceTransform()
        if dt is None:
            self._shape = self._path
            return None
        v = dt.map(QtCore.QPointF(1, 0)) - dt.map(QtCore.QPointF(0, 0))
        va = atan2(v.y(), v.x())
        dti = fn.invertQTransform(dt)
        devPos = dt.map(QtCore.QPointF(0, 0))
        tr = QtGui.QTransform()
        tr.translate(devPos.x(), devPos.y())
        tr.rotate(va * 180.0 / pi)
        return dti.map(tr.map(self._path))

    def mouseDragEvent(self, ev):
        if not self.movable or int(ev.button() & QtCore.Qt.LeftButton) == 0:
            return
        ev.accept()
        if ev.isStart():
            self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
            self.moving = True

        if not self.moving:
            return
        self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))

        if ev.isFinish():
            self.moving = False
            self.sigPositionChangeFinished.emit(self)

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            self.moving = False
            self.sigPositionChanged.emit(self)
            self.sigPositionChangeFinished.emit(self)

    def setMouseHover(self, hover):
        # Inform the item that the mouse is(not) hovering over it
        if self.mouseHovering is hover:
            return
        self.mouseHovering = hover
        if hover:
            self.currentBrush = self.hoverBrush
            self.currentPen = self.hoverPen
        else:
            self.currentBrush = self.brush
            self.currentPen = self.pen
        self.update()

    def hoverEvent(self, ev):
        if self.movable and (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            self.setMouseHover(True)
        else:
            self.setMouseHover(False)

    def viewTransformChanged(self):
        GraphicsObject.viewTransformChanged(self)
        self._shape = None  # invalidate shape, recompute later if requested.
        self.update()

    def position(self):
        return self._pos

    def _updateLabel(self):
        if self.label is None:
            return
        self.label.valueChanged()


class TargetLabel(TextItem):
    """A TextItem that attaches itself to a CursorItem.

    This class extends TextItem with the following features :
    * Automatically positions adjacent to the cursor at a fixed position.
    * Automatically reformats text when the cursor location has changed.

    Parameters
    ----------
    target : TargetItem
        The TargetItem to which this label will be attached to.
    text : str or callable
        Governs the text displayed, can be a fixed string or a format string
        that accepts the x, and y position of the target item; or be a callable
        method that accepts that returns a string to be displayed.
        Default is "x = {:0.3f}, y = {:0.3f}".
    offset : tuple or list or QPointF or QPoint
        Position to set the anchor of the TargetLabel away from the center of
        the target, by default it is (2, 0).
    anchor : tuple, list, QPointF or QPoint
        Position to rotate the TargetLabel about, and position to set the
        offset value to see :class:`~pyqtgraph.TextItem` for more inforation.
    angle : numeric
        Angle in degrees to rotate text about the anchor point. Default is 0;
        text will be displayed upright.
    kwargs : dict of arguments that are passed on to
        :class:`~pyqtgraph.TextItem` constructor, excluding text parameter
    """

    def __init__(
        self,
        target,
        text="x = {:0.3f}, y = {:0.3f}",
        offset=(2, 0),
        anchor=(0, 0.5),
        angle=0,
        **kwargs,
    ):
        super().__init__(anchor=anchor, angle=angle, **kwargs)
        self.setParentItem(target)
        self.target = target
        self.format = text
        if isinstance(offset, (tuple, list)):
            self.setPos(*offset)
        elif isinstance(offset, (QtCore.QPoint, QtCore.QPointF)):
            self.setPos(offset)
        else:
            raise TypeError("Offset parameter is the wrong data type")
        self.target.sigPositionChanged.connect(self.valueChanged)
        self.valueChanged()

    def valueChanged(self):
        x, y = self.target.position()
        if isinstance(self.format, str):
            self.setText(self.format.format(x, y))
        elif callable(self.format):
            self.setText(self.format(x, y))
