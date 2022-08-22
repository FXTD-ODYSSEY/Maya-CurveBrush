# -*- coding: utf-8 -*-
"""
Only support Maya2020 or upper version.
Not support Command Undo.

Only OpenMaya2.0 in Maya2020 or latest version support `MUIDrawManager`
Utilize MUIDrawManager can draw anything you like.
however the OpenMaya2.0 isn't complete yet.

`MPxContextCommand` lack of `syntax` `parser` fucntion
I have no idea how to establish a command query or edit logic.

`MPxToolCommand` `doFinalize` not support argument.
I have no idea how to make command undoable.

--- Test Code ---

from maya import cmds
cmds.file(f=1, new=1)

if cmds.pluginInfo('om2_curve_brush',q=1,l=1):
    cmds.unloadPlugin('om2_curve_brush')
cmds.loadPlugin("om2_curve_brush.py")

cmds.circle(s=100)
ctx = cmds.om2CurveBrushContext()
cmds.setToolTo(ctx)
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2022-08-02 15:40:31"

import sys
import inspect
from collections import defaultdict

from maya.api import OpenMaya as om
from maya.api import OpenMayaRender as omr
from maya.api import OpenMayaUI as omui
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

maya_useNewAPI = True

FLAG_TYPES = ("edit", "query", "create")
GETTER_MAP = {
    om.MSyntax.kDouble: "flagArgumentDouble",
    om.MSyntax.kUnsigned: "flagArgumentInt",
    om.MSyntax.kBoolean: "flagArgumentBool",
    om.MSyntax.kString: "flagArgumentString",
}


class BrushConfig(object):
    def __init__(self):
        self._size = 50
        self._strength = 15

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def strength(self):
        return self._strength

    @strength.setter
    def strength(self, value):
        self._strength = value


class DragMode:
    normal = 0
    brush = 1


class KeyListener(QtCore.QObject):
    def __init__(self, context):
        super(KeyListener, self).__init__()
        self.context = context

    def eventFilter(self, receivers, event):
        if isinstance(event, QtGui.QKeyEvent):
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_B:
                    self.context.drag_mode = DragMode.brush
            elif event.type() == QtCore.QEvent.KeyRelease:
                if self.context.drag_mode != DragMode.normal:
                    self.context.drag_mode = DragMode.normal
        return False


class CurveBrushContext(omui.MPxContext):
    """
    This context class extends a bounding box as the user drags the cursor during a selection
    opeartion.
    """

    HELP_STRING = "Click and drag to sculpt curve"

    @classmethod
    def creator(cls):
        """
        Create and return an instance of the LassoToolContext class.
        """
        return cls()

    def __init__(self):
        super(CurveBrushContext, self).__init__()
        self.view = None
        self.crv_dag_path_array = om.MDagPathArray()
        self.drag_mode = DragMode.normal
        self.pos_x = self.pos_y = 0
        self.brush_config = BrushConfig()
        self.start_brush_size = 0
        self.start_brush_strength = 0
        self.is_falloff_enabled = True
        self.key_listener = KeyListener(self)

        self.setTitleString("Curve Brush Tool")
        # Set the initial state of the cursor.
        self.setCursor(omui.MCursor.kDefaultCursor)
        # Tell the context which XPM to use.
        self.setImage("pythonFamily.png", omui.MPxContext.kImage1)

    def stringClassName(self):
        """
        Return the class name string.
        """
        return "curveBrush"

    def toolOnSetup(self, event):
        """
        Perform any setup operations when the tool is created.  In this case,
        set the help string.
        """
        self.setHelpString(CurveBrushContext.HELP_STRING)
        self.view = omui.M3dView.active3dView()
        app = QtWidgets.QApplication.instance()
        app.installEventFilter(self.key_listener)

        self.crv_dag_path_array.clear()
        itr = om.MItSelectionList(
            om.MGlobal.getActiveSelectionList(), om.MFn.kNurbsCurve
        )
        while not itr.isDone():
            self.crv_dag_path_array.append(itr.getDagPath())
            itr.next()
        if self.crv_dag_path_array.length() == 0:
            om.MGlobal.displayWarning("No NURBS Curve selected.")

    def toolOffCleanup(self):
        app = QtWidgets.QApplication.instance()
        app.removeEventFilter(self.key_listener)

    def doPress(self, event, drawMgr, context):
        """
        Handle the mouse press event in VP2.0.
        """
        self.view = omui.M3dView.active3dView()
        self.pos_x, self.pos_y = event.position
        self.start_brush_size = self.brush_config.size
        self.start_brush_strength = self.brush_config.strength

    def doRelease(self, event, drawMgr, context):
        """
        Handle the release press event in VP2.0.
        """
        self.view.refresh(False, True)

    def doDrag(self, event, draw_mgr, context):
        """
        Handle the mouse drag event in VP2.0.
        """
        self.view.refresh(False, True)

        curr_pos_x, curr_pos_y = event.position
        current_pos = om.MPoint(curr_pos_x, curr_pos_y)
        start = om.MPoint(self.pos_x, self.pos_y)
        delta = current_pos - start

        # Draw the lasso.
        draw_mgr.beginDrawable()
        draw_mgr.setColor(om.MColor((1.0, 1.0, 1.0)))
        draw_mgr.setLineWidth(2.0)
        if self.drag_mode == DragMode.brush:
            if event.mouseButton() == event.kLeftMouse:
                delta_val = delta.length() if delta.x > 0 else -delta.length()
                self.brush_config.size = self.start_brush_size + delta_val
                info = "Brush Size: %s" % self.brush_config.size
                draw_mgr.text2d(current_pos, info)
            elif event.mouseButton() == event.kMiddleMouse:
                delta_val = delta.length() if delta.y > 0 else -delta.length()
                self.brush_config.strength = self.start_brush_strength + delta_val
                info = "Brush Strength: %s" % self.brush_config.strength
                draw_mgr.text2d(current_pos, info)

            end_point = om.MPoint(
                self.pos_x, self.pos_y + self.brush_config.strength * 2
            )
            draw_mgr.line2d(start, end_point)
        else:
            startNearPos = om.MPoint()
            startFarPos = om.MPoint()
            currNearPos = om.MPoint()
            currFarPos = om.MPoint()

            self.view.viewToWorld(curr_pos_x, curr_pos_y, currNearPos, currFarPos)
            self.view.viewToWorld(self.pos_x, self.pos_y, startNearPos, startFarPos)

            cmd = CurveBrushTool()
            cmd.strength = self.brush_config.strength
            cmd.radius = self.brush_config.size
            cmd.move_vector = (currFarPos - startFarPos).normal()
            cmd.start_point = start
            cmd.dag_path_array = self.crv_dag_path_array
            cmd.redoIt()

        draw_mgr.circle2d(start, self.brush_config.size)
        draw_mgr.endDrawable()

    def doPtrMoved(self, event, draw_mgr, context):
        x, y = event.position
        screen_point = om.MPoint(x, y)
        radius = self.brush_config.size

        draw_mgr.beginDrawable()
        segment_count = 100
        if self.is_falloff_enabled:
            for dag_path in self.crv_dag_path_array:
                curve_fn = om.MFnNurbsCurve(dag_path)

                colorArray = om.MColorArray()
                pointArray = om.MPointArray()
                for point_index in range(segment_count):
                    param = curve_fn.findParamFromLength(
                        curve_fn.length() * point_index / segment_count
                    )
                    point = curve_fn.getPointAtParam(param, om.MSpace.kWorld)
                    pointArray.append(point)
                    x, y, _ = self.view.worldToView(point)
                    crv_point = om.MPoint(x, y)
                    distance = (crv_point - screen_point).length()
                    rgb = 1 - distance / radius
                    colorArray.append(
                        om.MColor((0.0, 0.0, 0.0, 0.0))
                        if distance > radius
                        else om.MColor((rgb, rgb, rgb))
                    )
                draw_mgr.setLineWidth(12.0)
                draw_mgr.mesh(
                    omr.MUIDrawManager.kLineStrip, pointArray, None, colorArray
                )

        draw_mgr.setColor(om.MColor((1.0, 1.0, 1.0)))
        draw_mgr.setLineWidth(2.0)
        draw_mgr.circle2d(screen_point, radius)
        draw_mgr.endDrawable()

    def doEnterRegion(self, event):
        """
        Handle the enter region event.  This method is called from both VP2.0 and the Legacy Viewport.
        """
        self.setHelpString(CurveBrushContext.HELP_STRING)


class CurveBrushContextCmd(omui.MPxContextCommand):
    """
    MPxContextCommand lack of `syntax` `parser` function
    """

    FLAGS_DATA = {
        "-r": {"long": "-radius", "type": om.MSyntax.kDouble},
        "-s": {"long": "-strength", "type": om.MSyntax.kDouble},
    }

    @classmethod
    def creator(cls):
        return cls()

    def makeObj(self):
        self.context = CurveBrushContext()
        return self.context

    # def __init__(self):
    #     super(CurveBrushContextCmd, self).__init__()
    #     self.flags_data = self.FLAGS_DATA.copy()
    #     for name, func in inspect.getmembers(self, inspect.ismethod):
    #         if name.startswith(tuple("flag_%s_" % typ for typ in FLAG_TYPES)):
    #             _, flag_type, flag = name.split("_")
    #             self.flags_data["-{0}".format(flag)][flag_type] = func

    # def doEditFlags(self):
    #     parser = self.parser()
    #     for flag, config in self.flags_data.items():
    #         callback = config.get("edit")
    #         if callable(callback) and parser.isFlagSet(flag):
    #             getter = getattr(parser, GETTER_MAP.get(config.get("type")))
    #             value = getter(flag, 0)
    #             callback(value)

    # def flag_edit_r(self, value):
    #     self.context.brush_config.size = value

    # def flag_edit_s(self, value):
    #     self.context.brush_config.strength = value

    # def doQueryFlags(self):
    #     parser = self.parser()
    #     for flag, config in self.flags_data.items():
    #         callback = config.get("query")
    #         if callable(callback) and parser.isFlagSet(flag):
    #             callback()

    # def flag_query_r(self):
    #     self.setResult(self.context.brush_config.size)

    # def flag_query_s(self):
    #     self.setResult(self.context.brush_config.strength)

    # def appendSyntax(self):
    #     syntax = self.syntax()
    #     for flag, config in self.flags_data.items():
    #         long_flag = config.get("long")
    #         flag_type = config.get("type")
    #         syntax.addFlag(flag, long_flag, flag_type)


class CurveBrushTool(omui.MPxToolCommand):
    FLAGS_DATA = {
        "-r": {"long": "-radius", "type": om.MSyntax.kDouble},
        "-s": {"long": "-strength", "type": om.MSyntax.kDouble},
    }

    @classmethod
    def creator(cls):
        return cls()

    def __init__(self):
        super(CurveBrushTool, self).__init__()
        self.radius = 0
        self.strength = 0
        self.move_vector = None
        self.start_point = None
        self.dag_path_array = None
        self.cv_pos_map = defaultdict(dict)

        self.commandString = self.__class__.__name__

        self.flags_data = self.FLAGS_DATA.copy()
        for name, func in inspect.getmembers(self, inspect.ismethod):
            if name.startswith(tuple("flag_%s_" % typ for typ in FLAG_TYPES)):
                _, flag_type, flag = name.split("_")
                self.flags_data["-{0}".format(flag)][flag_type] = func

    @classmethod
    def newSyntax(cls):
        syntax = om.MSyntax()
        for flag, config in cls.FLAGS_DATA.items():
            long_flag = config.get("long")
            flag_type = config.get("type")
            syntax.addFlag(flag, long_flag, flag_type)
        return syntax

    def appendSyntax(self):
        syntax = self.syntax()
        for flag, config in self.flags_data.items():
            syntax.addFlag(flag, config["long"], config["type"])

    def doIt(self, args):

        arg_db = om.MArgDatabase(self.syntax(), args)
        for flag, config in self.flags_data.items():
            callback = config.get("create")
            if callable(callback) and arg_db.isFlagSet(flag):
                getter = getattr(arg_db, GETTER_MAP.get(config.get("type")))
                value = getter(flag, 0)
                callback(value)
        return self.redoIt()

    def redoIt(self):
        offset_vector = self.move_vector * 0.002 * self.strength
        view = omui.M3dView.active3dView()
        for index, dag in enumerate(self.dag_path_array):
            curve_fn = om.MFnNurbsCurve(dag)
            point_array = curve_fn.cvPositions()
            for cv_index, pos in enumerate(point_array):
                x_pos, y_pos, _ = view.worldToView(pos)
                self.cv_pos_map[index][cv_index] = pos
                if (self.start_point - om.MPoint(x_pos, y_pos)).length() < self.radius:
                    try:
                        curve_fn.setCVPosition(
                            cv_index, pos + offset_vector, om.MSpace.kWorld
                        )
                    except:
                        pass
            curve_fn.updateCurve()

    def undoIt(self):
        for index, collections in self.cv_pos_map.items():
            curve_fn = om.MFnNurbsCurve(self.dag_path_array[index])
            for cv_index, pos in collections.items():
                curve_fn.setCVPosition(cv_index, pos, om.MSpace.kWorld)

    def isUndoable(self):
        return True

    # def finalize(self):
    #     command = om.MArgList()
    #     command.addArg(self.commandString)
    #     for flag, config in self.flags_data.items():
    #         long_flag = config.get("long")
    #         command.addArg(flag)
    #         command.addArg(getattr(self, long_flag[1:]))
    #     # TODO(timmyliang): not accept the command argument
    #     return self.doFinalize(command)

    def flag_create_r(self, value):
        self.radius = value

    def flag_create_s(self, value):
        self.strength = value


CONTEXT_NAME = "om2CurveBrushContext"
CONTEXT_TOOL_NAME = "c" + CurveBrushTool.__name__[1:]

# Initialize the plug-in
def initializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.registerContextCommand(CONTEXT_NAME, CurveBrushContextCmd.creator)
        # TODO(timmyliang): not support MPxToolCommand registered
        # pluginFn.registerContextCommand(
        #     CONTEXT_NAME,
        #     CurveBrushContextCmd.creator,
        #     CONTEXT_TOOL_NAME,
        #     CurveBrushTool.creator,
        #     CurveBrushTool.newSyntax,
        # )
    except:
        sys.stderr.write("Failed to register command: %s\n" % CONTEXT_NAME)
        raise


# Uninitialize the plug-in
def uninitializePlugin(plugin):
    pluginFn = om.MFnPlugin(plugin)
    try:
        pluginFn.deregisterContextCommand(CONTEXT_NAME)
    except:
        sys.stderr.write("Failed to unregister command: %s\n" % CONTEXT_NAME)
        raise
