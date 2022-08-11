# -*- coding: utf-8 -*-
"""
Curve Brush Tweak curve. 
OpenMaya1.0 not support OpenMaya2.0. (`doDrag` not work)
So it is not be able to draw feedback to the viewport.
But we can use the QWidget Overlay to draw such feedback.



--- Test Code ---

from maya import cmds
cmds.file(f=1, new=1)

if cmds.pluginInfo('om1_curve_brush',q=1,l=1):
    cmds.unloadPlugin('om1_curve_brush')
cmds.loadPlugin(r"F:\repo\CMakeMaya\modules\Maya-CurveBrush\plug-ins\om1_curve_brush.py")

cmds.circle(s=100)
ctx = cmds.curveBrushContext()
cmds.setToolTo(ctx)
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from collections import Iterable
from collections import defaultdict
from contextlib import contextmanager
import inspect
import logging
import math
import sys

# Import third-party modules
from Qt import QtCompat
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
from maya import OpenMaya
from maya import OpenMayaMPx
from maya import OpenMayaUI
from maya import cmds
from pymel import core as pm
import six


logging.basicConfig()
logger = logging.getLogger("CurveBrush")
logger.setLevel(logging.DEBUG)

FLAG_TYPES = ("edit", "query", "create")
GETTER_MAP = {
    OpenMaya.MSyntax.kDouble: "flagArgumentDouble",
    OpenMaya.MSyntax.kUnsigned: "flagArgumentInt",
    OpenMaya.MSyntax.kBoolean: "flagArgumentBool",
    OpenMaya.MSyntax.kString: "flagArgumentString",
}
FLAGS_DATA = {
    "-r": {"long": "-radius", "type": OpenMaya.MSyntax.kDouble},
    "-s": {"long": "-strength", "type": OpenMaya.MSyntax.kDouble},
}


def get_active_viewport():
    # type: () -> QtWidgets.QWidget
    view = OpenMayaUI.M3dView.active3dView()
    return QtCompat.wrapInstance(int(view.widget()), QtWidgets.QWidget)


def world_to_view(position, invertY=True):
    """
    convert the given 3d position to  2d viewport coordinates
    """
    view = OpenMayaUI.M3dView.active3dView()
    arg_x = OpenMaya.MScriptUtil(0)
    arg_y = OpenMaya.MScriptUtil(0)

    arg_x_ptr = arg_x.asShortPtr()
    arg_y_ptr = arg_y.asShortPtr()
    view.worldToView(position, arg_x_ptr, arg_y_ptr)
    x_pos = arg_x.getShort(arg_x_ptr)
    y_pos = arg_y.getShort(arg_y_ptr)

    if invertY:
        y_pos = view.portHeight() - y_pos

    return (x_pos, y_pos)


class KeyboardFilter(QtCore.QObject):
    key_pressed = QtCore.Signal(QtCore.QEvent)
    key_released = QtCore.Signal(QtCore.QEvent)

    def eventFilter(self, receiver, event):
        if isinstance(event, QtGui.QKeyEvent) and not event.isAutoRepeat():
            if event.type() == QtCore.QEvent.KeyPress:
                self.key_pressed.emit(event)
            elif event.type() == QtCore.QEvent.KeyRelease:
                self.key_released.emit(event)

        return super(KeyboardFilter, self).eventFilter(receiver, event)


class MouseFilter(QtCore.QObject):
    wheel = QtCore.Signal(QtCore.QEvent)
    moved = QtCore.Signal(QtCore.QEvent)
    clicked = QtCore.Signal(QtCore.QEvent)
    dragged = QtCore.Signal(QtCore.QEvent)
    released = QtCore.Signal(QtCore.QEvent)
    entered = QtCore.Signal()
    leaved = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(MouseFilter, self).__init__(*args, **kwargs)
        self.is_clicked = False

    def eventFilter(self, receiver, event):
        event_type = event.type()
        if event_type == QtCore.QEvent.MouseMove:
            self.moved.emit(event)
            if self.is_clicked:
                self.dragged.emit(event)
        elif (
            event_type == QtCore.QEvent.MouseButtonPress
            or event_type == QtCore.QEvent.MouseButtonDblClick
        ):
            self.is_clicked = True
            self.clicked.emit(event)
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self.is_clicked = False
            self.released.emit(event)
        elif event_type == QtCore.QEvent.Enter:
            self.entered.emit()
        elif event_type == QtCore.QEvent.Leave:
            self.leaved.emit()
        elif event_type == QtCore.QEvent.Wheel:
            self.wheel.emit(event)

        return super(MouseFilter, self).eventFilter(receiver, event)


class AppFilter(QtCore.QObject):
    def __init__(self, canvas):
        # type: (CurveBrushContext) -> None
        super(AppFilter, self).__init__()
        self.canvas = canvas

    def eventFilter(self, receiver, event):
        if event.type() in [QtCore.QEvent.MouseButtonPress]:
            widget = QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos())
            panel = isinstance(widget, QtCore.QObject) and widget.parent()
            name = panel and panel.objectName()
            if name:
                is_model_editor = cmds.objectTypeUI(name, i="modelEditor")
                self.canvas.setVisible(is_model_editor)
                if is_model_editor:
                    QtCore.QTimer.singleShot(0, self.canvas.setup_active_viewport)
        return super(AppFilter, self).eventFilter(receiver, event)


class CanvasOverlay(QtWidgets.QWidget):
    """Refernce from spore Canvas."""

    resized = QtCore.Signal(QtCore.QEvent)
    moved = QtCore.Signal(QtCore.QEvent)
    tool_setup = QtCore.Signal()
    tool_cleanup = QtCore.Signal()

    def eventFilter(self, receiver, event):
        if event.type() == QtCore.QEvent.Resize:
            self.resized.emit(event)
        elif event.type() == QtCore.QEvent.Move:
            self.moved.emit(event)
        return super(CanvasOverlay, self).eventFilter(receiver, event)

    @property
    def radius(self):
        return self.context.radius

    @radius.setter
    def radius(self, value):
        self.context.radius = value if value > 0 else 0

    @property
    def strength(self):
        return self.context.strength

    @strength.setter
    def strength(self, value):
        self.context.strength = value if value > 0 else 0

    @property
    def message_info(self):
        return self._message_info

    @strength.setter
    def message_info(self, value):
        self._message_info = str(value)

        def reset_message_info():
            self._message_info = ""

        # NOTES(timmyliang): reset message_info after 2 seconds
        QtCore.QTimer.singleShot(2000, reset_message_info)

    def __init__(self, context):
        # type: (CurveBrushContext) -> None
        super(CanvasOverlay, self).__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.SplashScreen
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        self.context = context
        self.viewport = None
        self.viewport_window = None
        self.start_pos = QtCore.QPoint()
        self.current_pos = QtCore.QPoint()
        self.is_press_B = False
        self.is_press_alt = True
        self.is_falloff_enabled = True
        self.color_data = defaultdict(dict)
        self.press_button = None
        self._message_info = ""
        self.curves = []

        self.mouse_filter = MouseFilter()
        self.mouse_filter.moved.connect(self.move_mouse)
        self.mouse_filter.dragged.connect(self.drag_mouse)
        self.mouse_filter.clicked.connect(self.press_mouse)
        self.mouse_filter.released.connect(self.release_mouse)
        self.mouse_filter.entered.connect(lambda: self.setVisible(True))
        self.mouse_filter.leaved.connect(lambda: self.setVisible(False))
        self.mouse_filter.wheel.connect(self.move_mouse)

        self.keyboard_filter = KeyboardFilter()
        self.keyboard_filter.key_pressed.connect(self.press_key)
        self.keyboard_filter.key_released.connect(self.release_key)

        self.app_filter = AppFilter(self)
        self.maya_window = pm.uitypes.toQtObject("MayaWindow")
        self.tool_setup.connect(self._setup_tool)
        self.tool_cleanup.connect(self._cleanup_tool)
        self.resized.connect(self._resize_overlay)
        self.moved.connect(self._resize_overlay)

    def _setup_tool(self):
        self.curves = [
            sel for sel in pm.ls(sl=1) if isinstance(sel.getShape(), pm.nt.NurbsCurve)
        ]
        if not self.curves:
            pm.warning("No NURBS Curve selected.")
            return

        app = QtWidgets.QApplication.instance()
        app.installEventFilter(self.app_filter)
        self.maya_window.installEventFilter(self.keyboard_filter)

        self.setup_active_viewport()

    def _cleanup_tool(self):
        if not self.curves:
            return

        app = QtWidgets.QApplication.instance()
        app.removeEventFilter(self.app_filter)
        self.maya_window.removeEventFilter(self.keyboard_filter)

        self.setVisible(False)
        self.cleanup_event_filter()

    def _resize_overlay(self):
        if not QtCompat.isValid(self.viewport):
            return
        parent = self.viewport
        self.move(parent.mapToGlobal(parent.pos()))
        viewport_geo = parent.geometry()
        self.setFixedWidth(viewport_geo.width())
        self.setFixedHeight(viewport_geo.height())

    def cleanup_event_filter(self, widgets=None):
        for widget in widgets or [self.viewport, self.viewport_window]:
            if widget and QtCompat.isValid(widget):
                widget.removeEventFilter(self)
                widget.removeEventFilter(self.mouse_filter)

    def setup_active_viewport(self):
        viewport = get_active_viewport()
        if self.viewport == viewport:
            return

        self.cleanup_event_filter()
        self.viewport = viewport
        self.viewport_window = viewport.window()

        self.viewport.installEventFilter(self)
        self.viewport.installEventFilter(self.mouse_filter)

        self.viewport_window.installEventFilter(self)
        self._resize_overlay()

    def press_key(self, event):
        if event.key() == QtCore.Qt.Key_B:
            self.start_pos = self.viewport.mapFromGlobal(QtGui.QCursor.pos())
            self.is_press_B = True

        if event.modifiers() == QtCore.Qt.AltModifier:
            self.is_press_alt = True

    def release_key(self, event):
        self.is_press_alt = False
        if event.key() == QtCore.Qt.Key_B:
            self.is_press_B = False

    def press_mouse(self, event):
        self.start_pos = event.pos()
        self.press_button = event.button()
        self.start_raidus = self.radius
        self.start_strength = self.strength

    def release_mouse(self, event):
        pass

    def drag_mouse(self, event):
        current_pos = event.pos()
        delta = current_pos - self.start_pos
        if self.is_press_B:
            delta_val = delta.manhattanLength()
            if self.press_button == QtCore.Qt.LeftButton:
                delta_val = delta_val if delta.x() > 0 else -delta_val
                self.radius = self.start_raidus + delta_val
                self.message_info = "Brush Size: %s" % self.radius
            elif self.press_button == QtCore.Qt.MiddleButton:
                delta_val = delta_val if delta.y() < 0 else -delta_val
                self.strength = self.start_strength + delta_val
                self.message_info = "Brush Strength: %s" % self.strength
        # NOTE(timmyliang): ignore alt orbit camera
        elif not self.is_press_alt:
            startNearPos = OpenMaya.MPoint()
            startFarPos = OpenMaya.MPoint()
            currNearPos = OpenMaya.MPoint()
            currFarPos = OpenMaya.MPoint()

            view = OpenMayaUI.M3dView.active3dView()
            # NOTES(timmyliang): QPoint need to minus y as MPoint
            view.viewToWorld(current_pos.x(), -current_pos.y(), currNearPos, currFarPos)
            view.viewToWorld(
                self.start_pos.x(), -self.start_pos.y(), startNearPos, startFarPos
            )

            ptr = self.context._newToolCommand()
            cmd = CurveBrushTool.instance_dict.get(OpenMayaMPx.asHashable(ptr))
            cmd.strength = self.strength
            cmd.radius = self.radius
            cmd.move_vector = (currFarPos - startFarPos).normal()
            cmd.start_point = OpenMaya.MPoint(self.start_pos.x(), self.start_pos.y())
            cmd.curves = self.curves
            cmd.redoIt()
            cmd.finalize()
            view.refresh(False, True)

        self.update()

    def move_mouse(self, event):
        self.current_pos = event.pos()
        self.color_data.clear()
        if self.is_falloff_enabled:
            segment_count = 100
            for curve in self.curves:
                crv = pm.PyNode(curve).getShape().__apimfn__()
                points = []
                colors = []
                for point_index in range(segment_count):
                    percent = crv.length() * point_index / segment_count
                    param = crv.findParamFromLength(percent)
                    point = OpenMaya.MPoint()
                    crv.getPointAtParam(param, point, OpenMaya.MSpace.kWorld)
                    x, y = world_to_view(point)
                    crv_point = QtCore.QPoint(x, y)
                    points.append(crv_point)
                    distance = (crv_point - self.current_pos).manhattanLength()
                    rgb = 1 - distance / self.radius
                    colors.append(
                        QtGui.QColor.fromRgbF(rgb,rgb, rgb)
                        if distance < self.radius
                        else QtGui.QColor.fromRgbF(0,0, 0,0)
                    )
                points.append(points[0])
                colors.append(colors[0])
                # temp = -1
                self.color_data[curve] = {"colors": colors, "points": points}
        self.update()

    def paintEvent(self, event):
        self.draw_shape(self.create_brush_cricle(), QtCore.Qt.white, 2)
        if self.is_press_B:
            self.draw_shape(self.create_brush_line(), QtCore.Qt.white, 2)
        self.draw_text(self._message_info)
        for curve, data in self.color_data.items():
            self.draw_shape(data.get("points"), data.get("colors"), 10)

        return super(CanvasOverlay, self).paintEvent(event)

    def create_brush_cricle(self, count=60):
        shape = []
        radius = self.radius
        pt = self.start_pos if self.is_press_B else self.current_pos
        for index in range(count + 1):
            theta = math.radians(360 * index / count)
            pos_x = pt.x() + radius * math.cos(theta)
            pos_y = pt.y() + radius * math.sin(theta)
            shape.append(QtCore.QPointF(pos_x, pos_y))
        return shape

    def create_brush_line(self):
        shape = []
        start_pt = self.start_pos if self.is_press_B else self.current_pos
        shape.append(start_pt)
        shape.append(QtCore.QPoint(start_pt.x(), start_pt.y() - self.strength))
        return shape

    def draw_shape(self, line_shapes, colors, width=1):
        if len(line_shapes) < 2:
            return
        colors = colors or QtCore.Qt.white
        painter = QtGui.QPainter(self)

        painter.setRenderHint(painter.Antialiasing)
        painter.begin(self)

        if isinstance(colors, Iterable) and not isinstance(colors, six.string_types):
            for index, point in enumerate(line_shapes[:-1]):
                start_point = point
                end_point = line_shapes[index+1]
                grandient_color = QtGui.QLinearGradient(start_point,end_point)
                start_color = colors[index]
                end_color = colors[index+1]
                grandient_color.setColorAt(0, start_color)
                grandient_color.setColorAt(1, end_color)
                pen = QtGui.QPen(grandient_color, width)
                pen.setCapStyle(QtCore.Qt.RoundCap)
                pen.setJoinStyle(QtCore.Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(start_point,end_point)
        else:
            path = QtGui.QPainterPath()
            path.moveTo(line_shapes[0])
            [path.lineTo(point) for point in line_shapes]
            color = QtGui.QColor(colors)
            pen = QtGui.QPen(color, width)
            painter.setPen(pen)
            painter.drawPath(path)
    
        painter.end()

    def draw_text(self, text, pos=None, color=QtCore.Qt.white, width=1):
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(color, width)
        painter.setPen(pen)
        pos = pos or self.current_pos + QtCore.QPoint(10, 0)
        painter.drawText(pos, text)
        painter.end()


class CurveBrushContext(OpenMayaMPx.MPxContext):

    TITLE = "Curve Brush Context"
    HELP_TEXT = "Curve Brush Context."

    def __init__(self):
        super(CurveBrushContext, self).__init__()
        self._setTitleString(self.TITLE)
        self.setImage("pythonFamily.png", OpenMayaMPx.MPxContext.kImage1)

        self.radius = 50
        self.strength = 15

        self.canvas = CanvasOverlay(self)

    def helpStateHasChanged(self, event):
        self._setHelpString(self.HELP_TEXT)

    def stringClassName(self):
        """Return the class name string."""
        return "curveBrush"

    def toolOnSetup(self, event):
        self.canvas.tool_setup.emit()

    def toolOffCleanup(self):
        self.canvas.tool_cleanup.emit()


class CurveBrushContextCmd(OpenMayaMPx.MPxContextCommand):
    def __init__(self):
        super(CurveBrushContextCmd, self).__init__()
        self.context = None
        self.flags_data = FLAGS_DATA.copy()
        for name, func in inspect.getmembers(self, inspect.ismethod):
            if name.startswith(FLAG_TYPES):
                key, flag = name.split("_")
                self.flags_data["-{0}".format(flag)][key] = func

    @staticmethod
    def creator():
        return OpenMayaMPx.asMPxPtr(CurveBrushContextCmd())

    def makeObj(self):
        self.context = CurveBrushContext()
        return OpenMayaMPx.asMPxPtr(self.context)

    def appendSyntax(self):
        syntax = self._syntax()
        for flag, config in self.flags_data.items():
            syntax.addFlag(flag, config["long"], config["type"])

    def doEditFlags(self):
        if not self.context:
            return
        parser = self._parser()  # type: OpenMaya.MArgParser
        for flag, config in self.flags_data.items():
            callback = config.get("edit")
            if callable(callback) and parser.isFlagSet(flag):
                getter = getattr(parser, GETTER_MAP.get(config.get("type")))
                value = getter(flag, 0)
                callback(value)

    def flag_edit_r(self, value):
        self.context.state.stroke.radius = value
        self.context.canvas.update()

    def flag_edit_s(self, value):
        self.context.state.stroke.strength = value

    def doQueryFlags(self):
        if not self.context:
            return
        parser = self._parser()  # type: OpenMaya.MArgParser
        for flag, config in self.flags_data.items():
            callback = config.get("query")
            if callable(callback) and parser.isFlagSet(flag):
                callback()

    def flag_query_r(self):
        self.setResult(self.context.state.stroke.radius)

    def flag_query_s(self):
        self.setResult(self.context.state.stroke.strength)


class CurveBrushTool(OpenMayaMPx.MPxToolCommand):

    instance_dict = {}

    @classmethod
    def creator(cls):
        return OpenMayaMPx.asMPxPtr( cls())

    @classmethod
    def newSyntax(cls):
        syntax = OpenMaya.MSyntax()
        for flag, config in FLAGS_DATA.items():
            long_flag = config.get("long")
            flag_type = config.get("type")
            syntax.addFlag(flag, long_flag, flag_type)
        return syntax

    def __init__(self):
        super(CurveBrushTool, self).__init__()
        self.radius = 0
        self.strength = 0
        self.move_vector = None
        self.start_point = None
        self.curves = []
        self.cv_pos_map = defaultdict(dict)
        self.instance_dict[OpenMayaMPx.asHashable(self)] = self

        self.flags_data = FLAGS_DATA.copy()
        for name, func in inspect.getmembers(self, inspect.ismethod):
            if name.startswith(tuple("flag_%s_" % typ for typ in FLAG_TYPES)):
                _, flag_type, flag = name.split("_")
                self.flags_data["-{0}".format(flag)][flag_type] = func

    def commandString(self):
        return CONTEXT_TOOL_NAME

    def appendSyntax(self):
        syntax = self.syntax()
        for flag, config in self.flags_data.items():
            syntax.addFlag(flag, config["long"], config["type"])

    def doIt(self, args):

        arg_db = OpenMaya.MArgDatabase(self.syntax(), args)
        for flag, config in self.flags_data.items():
            callback = config.get("create")
            if callable(callback) and arg_db.isFlagSet(flag):
                getter = getattr(arg_db, GETTER_MAP.get(config.get("type")))
                value = getter(flag, 0)
                callback(value)
        return self.redoIt()

    def redoIt(self):
        offset_vector = self.move_vector * 0.002 * self.strength
        for index, curve in enumerate(self.curves):
            dag_path = pm.PyNode(curve).getShape().__apimdagpath__()
            itr = OpenMaya.MItCurveCV(dag_path)
            curve_fn = OpenMaya.MFnNurbsCurve(dag_path)

            offset_map = {}
            while not itr.isDone():
                cv_index = itr.index()
                pos = itr.position(OpenMaya.MSpace.kWorld)
                self.cv_pos_map[curve][cv_index] = pos
                cv_point = OpenMaya.MPoint(*world_to_view(pos))
                if (self.start_point - cv_point).length() < self.radius:
                    offset_map[cv_index] = pos + offset_vector

                itr.next()

            for index, pos in offset_map.items():
                curve_fn.setCV(index, pos, OpenMaya.MSpace.kWorld)

            curve_fn.updateCurve()

    def undoIt(self):
        for curve, collections in self.cv_pos_map.items():
            curve_fn = pm.PyNode(curve).getShape().__apimfn__()
            for cv_index, pos in collections.items():
                curve_fn.setCV(cv_index, pos, OpenMaya.MSpace.kWorld)

    def isUndoable(self):
        return True

    def finalize(self):
        command = OpenMaya.MArgList()
        command.addArg(self.commandString)
        for flag, config in self.flags_data.items():
            long_flag = config.get("long")
            command.addArg(flag)
            command.addArg(getattr(self, long_flag[1:]))
        return self._doFinalize(command)

    def flag_create_r(self, value):
        self.radius = value

    def flag_create_s(self, value):
        self.strength = value


@contextmanager
def try_run(name):
    try:
        yield name
    except:
        if name:
            sys.stderr.write("Failed to register: %s\n" % name)
        raise


CONTEXT_NAME = "c" + CurveBrushContext.__name__[1:]
CONTEXT_TOOL_NAME = "c" + CurveBrushTool.__name__[1:]

# Initialize the script plug-in
def initializePlugin(obj):

    plugin_fn = OpenMayaMPx.MFnPlugin(obj, "timmyliang", "1.0.0")

    with try_run(CONTEXT_NAME) as name:
        plugin_fn.registerContextCommand(
            name,
            CurveBrushContextCmd.creator,
            CONTEXT_TOOL_NAME,
            CurveBrushTool.creator,
            CurveBrushTool.newSyntax,
        )


# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)

    with try_run(CONTEXT_NAME) as name:
        plugin_fn.deregisterContextCommand(name, CONTEXT_TOOL_NAME)
