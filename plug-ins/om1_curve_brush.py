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
from contextlib import contextmanager
import logging
import inspect
import sys
import os

# Import third-party modules
from Qt import QtCore
from Qt import QtWidgets
from Qt import QtGui
from Qt import QtCompat
from maya import OpenMaya
from maya import OpenMayaUI
from maya import OpenMayaMPx
from pymel import core as pm
from maya import cmds

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


class KeyboardFilter(QtCore.QObject):
    key_press = QtCore.Signal(QtCore.QEvent)
    key_release = QtCore.Signal(QtCore.QEvent)

    def eventFilter(self, receiver, event):
        if isinstance(event, QtGui.QKeyEvent) and not event.isAutoRepeat():
            if event.type() == QtCore.QEvent.KeyPress:
                self.key_press.emit(event)
            elif event.type() == QtCore.QEvent.KeyRelease:
                self.key_release.emit(event)

        return super(KeyboardFilter, self).eventFilter(receiver, event)


class MouseFilter(QtCore.QObject):
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
        if (
            event_type == QtCore.QEvent.MouseButtonPress
            or event_type == QtCore.QEvent.MouseButtonDblClick
        ):
            self.is_clicked = True
            self.clicked.emit(event)
        if event_type == QtCore.QEvent.MouseButtonRelease:
            self.is_clicked = False
            self.released.emit(event)
        if event_type == QtCore.QEvent.Enter:
            self.entered.emit()
        if event_type == QtCore.QEvent.Leave:
            self.leaved.emit()

        return super(MouseFilter, self).eventFilter(receiver, event)


class AppFilter(QtCore.QObject):
    def __init__(self, context):
        # type: (CurveBrushContext) -> None
        super(AppFilter, self).__init__()
        self.context = context

    def eventFilter(self, receiver, event):
        if event.type() in [QtCore.QEvent.MouseButtonPress]:
            widget = QtWidgets.QApplication.widgetAt(QtGui.QCursor.pos())
            panel = isinstance(widget, QtCore.QObject) and widget.parent()
            name = panel and panel.objectName()
            if name:
                is_model_editor = cmds.objectTypeUI(name, i="modelEditor")
                self.context.canvas.setVisible(is_model_editor)
                if is_model_editor:
                    QtCore.QTimer.singleShot(
                        0, self.context.canvas.setup_active_viewport
                    )
                    # self.context.canvas.setup_active_viewport()
        return super(AppFilter, self).eventFilter(receiver, event)


class CanvasOverlay(QtWidgets.QWidget):
    """Refernce from spore Canvas."""

    resized = QtCore.Signal(QtCore.QEvent)
    moved = QtCore.Signal(QtCore.QEvent)

    def eventFilter(self, receiver, event):
        if event.type() == QtCore.QEvent.Resize:
            self.resized.emit(event)
        elif event.type() == QtCore.QEvent.Move:
            self.moved.emit(event)
        return super(CanvasOverlay, self).eventFilter(receiver, event)

    def get_active_viewport(self):
        view = OpenMayaUI.M3dView.active3dView()
        return QtCompat.wrapInstance(int(view.widget()), QtWidgets.QWidget)

    def __init__(self, context):
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
        self.resized.connect(self._resize_overlay)
        self.moved.connect(self._resize_overlay)

        self.mouse_filter = MouseFilter()
        self.mouse_filter.moved.connect(self.move_mouse)
        self.mouse_filter.dragged.connect(self.drag_mouse)
        self.mouse_filter.clicked.connect(self.press_mouse)
        self.mouse_filter.released.connect(self.release_mouse)
        self.mouse_filter.entered.connect(lambda: self.setVisible(True))
        self.mouse_filter.leaved.connect(lambda: self.setVisible(False))

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
        viewport = self.get_active_viewport()
        if self.viewport == viewport:
            return

        self.cleanup_event_filter()
        self.viewport = viewport
        self.viewport_window = viewport.window()

        self.viewport.installEventFilter(self)
        self.viewport.installEventFilter(self.mouse_filter)

        self.viewport_window.installEventFilter(self)
        self._resize_overlay()

    def press_mouse(self, event):
        pass
        # self.view = omui.M3dView.active3dView()
        # self.pos_x, self.pos_y = event.position
        # self.start_brush_size = self.brush_config.size
        # self.start_brush_strength = self.brush_config.strength

    def release_mouse(self, event):
        pass

    def drag_mouse(self, event):
        pass
        # curr_pos_x, curr_pos_y = event.position
        # current_pos = om.MPoint(curr_pos_x, curr_pos_y)
        # start = om.MPoint(self.pos_x, self.pos_y)
        # delta = current_pos - start

        # # Draw the lasso.
        # draw_mgr.beginDrawable()
        # draw_mgr.setColor(om.MColor((1.0, 1.0, 1.0)))
        # draw_mgr.setLineWidth(2.0)
        # if self.drag_mode == DragMode.brush:
        #     if event.mouseButton() == event.kLeftMouse:
        #         delta_val = delta.length() if delta.x > 0 else -delta.length()
        #         self.brush_config.size = self.start_brush_size + delta_val
        #         info = "Brush Size: %s" % self.brush_config.size
        #         draw_mgr.text2d(current_pos, info)
        #     elif event.mouseButton() == event.kMiddleMouse:
        #         delta_val = delta.length() if delta.y > 0 else -delta.length()
        #         self.brush_config.strength = self.start_brush_strength + delta_val
        #         info = "Brush Strength: %s" % self.brush_config.strength
        #         draw_mgr.text2d(current_pos, info)

        #     end_point = om.MPoint(
        #         self.pos_x, self.pos_y + self.brush_config.strength * 2
        #     )
        #     draw_mgr.line2d(start, end_point)
        # else:
        #     startNearPos = om.MPoint()
        #     startFarPos = om.MPoint()
        #     currNearPos = om.MPoint()
        #     currFarPos = om.MPoint()

        #     self.view.viewToWorld(curr_pos_x, curr_pos_y, currNearPos, currFarPos)
        #     self.view.viewToWorld(self.pos_x, self.pos_y, startFarPos, startFarPos)

        #     cmd = CurveBrushTool()
        #     cmd.strength = self.brush_config.strength
        #     cmd.radius = self.brush_config.size
        #     cmd.move_vector = (currFarPos - startFarPos).normal()
        #     cmd.start_point = start
        #     cmd.dag_path_array = self.crv_dag_path_array
        #     cmd.redoIt()

        # draw_mgr.circle2d(start, self.brush_config.size)
        # draw_mgr.endDrawable()

    def move_mouse(self, event):
        pass
        # qt_pos = event.pos()
        # screen_point = OpenMaya.MPoint(qt_pos.x(), qt_pos.y())
        # radius = self.brush_config.size

        # segment_count = 100
        # if self.is_falloff_enabled:
        #     for dag_path in self.crv_dag_path_array:
        #         curve_fn = om.MFnNurbsCurve(dag_path)

        #         colorArray = om.MColorArray()
        #         pointArray = om.MPointArray()
        #         for point_index in range(segment_count):
        #             param = curve_fn.findParamFromLength(
        #                 curve_fn.length() * point_index / segment_count
        #             )
        #             point = curve_fn.getPointAtParam(param, om.MSpace.kWorld)
        #             pointArray.append(point)
        #             x, y, _ = self.view.worldToView(point)
        #             crv_point = om.MPoint(x, y)
        #             distance = (crv_point - screen_point).length()
        #             rgb = 1 - distance / radius
        #             colorArray.append(
        #                 om.MColor((0.0, 0.0, 0.0, 0.0))
        #                 if distance > radius
        #                 else om.MColor((rgb, rgb, rgb))
        #             )
        #         draw_mgr.setLineWidth(12.0)
        #         draw_mgr.mesh(
        #             omr.MUIDrawManager.kLineStrip, pointArray, None, colorArray
        #         )

        # draw_mgr.setColor(om.MColor((1.0, 1.0, 1.0)))
        # draw_mgr.setLineWidth(2.0)
        # draw_mgr.circle2d(screen_point, radius)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        height = self.height()
        r = QtCore.QRect(0, self.height() - height, self.width(), height)
        painter.fillRect(r, QtGui.QBrush(QtCore.Qt.blue))
        pen = QtGui.QPen(QtGui.QColor("red"), 10)
        painter.setPen(pen)
        painter.drawRect(self.rect())

        return super(CanvasOverlay, self).paintEvent(event)


class CurveBrushContext(OpenMayaMPx.MPxContext):

    TITLE = "Curve Brush Context"
    HELP_TEXT = "Curve Brush Context."

    def __init__(self):
        """
        Initialize the members of the SquareScaleManipContext class.
        """
        super(CurveBrushContext, self).__init__()
        self._setTitleString(self.TITLE)
        self.setImage("pythonFamily.png", OpenMayaMPx.MPxContext.kImage1)

        self.view = OpenMayaUI.M3dView.active3dView()
        self.maya_window = pm.uitypes.toQtObject("MayaWindow")
        self.canvas = CanvasOverlay(self)

        self.keyboarad_filter = KeyboardFilter()
        self.mouse_filter = MouseFilter()
        self.app_filter = AppFilter(self)

    def helpStateHasChanged(self, event):
        self._setHelpString(self.HELP_TEXT)

    def stringClassName(self):
        """Return the class name string."""
        return "curveBrush"

    def toolOnSetup(self, event):
        app = QtWidgets.QApplication.instance()
        app.installEventFilter(self.app_filter)
        self.maya_window.installEventFilter(self.keyboarad_filter)

    def toolOffCleanup(self):
        app = QtWidgets.QApplication.instance()
        app.removeEventFilter(self.app_filter)
        self.maya_window.removeEventFilter(self.keyboarad_filter)

        self.canvas.setVisible(False)
        self.canvas.cleanup_event_filter()


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
        return CurveBrushContextCmd()

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


@contextmanager
def try_run(name):
    try:
        yield name
    except:
        if name:
            sys.stderr.write("Failed to register: %s\n" % name)
        raise


CONTEXT_NAME = "c" + CurveBrushContext.__name__[1:]

# Initialize the script plug-in
def initializePlugin(obj):

    plugin_fn = OpenMayaMPx.MFnPlugin(obj, "timmyliang", "1.0.0")

    with try_run(CONTEXT_NAME) as name:
        plugin_fn.registerContextCommand(name, CurveBrushContextCmd.creator)


# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)

    with try_run(CONTEXT_NAME) as name:
        plugin_fn.deregisterContextCommand(name)
