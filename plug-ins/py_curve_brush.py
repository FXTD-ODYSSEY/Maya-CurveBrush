# -*- coding: utf-8 -*-
"""
Curve Brush Tweak curve.
ctx = cmds.pyCurveBrushContext()
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
import _curve_brush
import attr
from maya import OpenMaya
from maya import OpenMayaUI
from maya import OpenMayaMPx
from pymel import core as pm

logging.basicConfig()
logger = logging.getLogger("CurveBrush")
logger.setLevel(logging.DEBUG)


class CurveBrushContext(OpenMayaMPx.MPxContext):

    TITLE = "Curve Brush Context"
    HELP_TEXT = "Curve Brush Context."

    def __init__(self):
        """
        Initialize the members of the SquareScaleManipContext class.
        """
        super(CurveBrushContext, self).__init__()
        self.setTitleString("Plug-in manipulator: " + self.__name__)
        
        self.view = OpenMayaUI.M3dView.active3dView()

        self.state = brush_state.BrushState()
        self.canvas = None
        self.is_reflect = False
        self.current_brush = None

        self._setTitleString(self.TITLE)
        self.setImage("../coins/tony_shop.png", OpenMayaMPx.MPxContext.kImage1)

        # mouse and key events for brush context
        self.mouseEventFilter = event_filter.MouseEventFilter(self)
        self.keyEventFilter = event_filter.KeyEventFilter(self)
        
        self.mouseEventFilter.clicked.connect(self.clicked)
        self.mouseEventFilter.released.connect(self.released)
        self.mouseEventFilter.dragged.connect(self.dragged)
        self.mouseEventFilter.mouseMoved.connect(self.mouseMoved)
        self.mouseEventFilter.enter.connect(self.enter)
        self.mouseEventFilter.leave.connect(self.leave)

        # key event signals
        self.keyEventFilter.bPressed.connect(self.bPressed)
        self.keyEventFilter.bReleased.connect(self.bReleased)
        self.keyEventFilter.keyPress.connect(self.keyPress)
        self.keyEventFilter.keyRelease.connect(self.keyRelease)

    def toolOnSetup(self, event):
        # install event filter
        view = window_utils.activeViewWdg()
        view.installEventFilter(self.mouseEventFilter)
        window = window_utils.mayaMainWindow()
        window.installEventFilter(self.keyEventFilter)

        # Set up canvas for drawing
        self.canvas = brush_ui.CircularBrush(self.state, None)
        
    def toolOffCleanup(self):
        view = window_utils.activeViewWdg()
        view.removeEventFilter(self.mouseEventFilter)
        window = window_utils.mayaMainWindow()
        window.removeEventFilter(self.keyEventFilter)

        self.state.draw = False

        if self.canvas:
            self.canvas.update()
            del self.canvas
            

    def helpStateHasChanged(self, event):
        self._setHelpString(self.HELP_TEXT)


    def mouseMoved(self, _position):
        # Retrive cursor position
        self.state.stroke.cursorX = _position.x()
        self.state.stroke.cursorY = _position.y()

        # Get hitTest result
        result = None
        reflect_result = None
        # If b is pressed(modifying the radius of brush), then using firstScale as cursor position
        if not self.state.stroke.firstScale:
            # First get the origin and direction of the ray from camera to mouse
            origin, direction = mesh_utils.get_camera_ray(
                self.state.stroke.firstX, self.state.stroke.firstY
            )
            # Second get the hit result by the ray
            result = mesh_utils.hitTest(self.state.mesh, origin, direction)
        else:
            origin, direction = mesh_utils.get_camera_ray(_position.x(), _position.y())
            result = mesh_utils.hitTest(self.state.mesh, origin, direction)
            if self.state.is_reflect and result:
                # OBJECT_Y is a special case to symmetry
                if self.state.symmetry == SymmetryType.OBJECT_Y:
                    reflect_origin = result[0]
                    reflect_origin = om.MPoint(
                        reflect_origin[0], reflect_origin[1], reflect_origin[2]
                    )
                    reflect_origin = reflect_origin - self.state.reflect_normal * 1000
                    reflect_direction = self.state.reflect_normal
                else:
                    reflect_origin, reflect_direction = mesh_utils.get_camera_ray(
                        _position.x(),
                        _position.y(),
                        self.state.is_reflect,
                        self.state.reflect_matrix,
                    )
                reflect_result = mesh_utils.hitTest(
                    self.state.mesh, reflect_origin, reflect_direction
                )

        # Retrive data from hitTest result
        if result:
            position, normal, tangent = result
            self.state.stroke.position = position
            self.state.stroke.normal = normal
            self.state.stroke.tangent = tangent
            self.state.stroke.isHit = True

            if (
                self.state.is_reflect
                and reflect_result
                and self.state.stroke.firstScale
            ):
                reflect_position, reflect_normal, reflect_tangent = reflect_result
                self.state.rStroke.position = reflect_position
                self.state.rStroke.normal = reflect_normal
                self.state.rStroke.tangent = reflect_tangent
                self.state.rStroke.isHit = True
            else:
                self.state.rStroke.isHit = False
        else:
            self.state.stroke.isHit = False

        if self.state.type == BrushType.SURFACE:
            if result:
                # Update stroke direction
                self.update_stroke(self.state.stroke, position)
                if self.state.is_reflect and reflect_result:
                    self.update_stroke(self.state.rStroke, reflect_position)

                # If there is any key pressed, do not operate guides anymore
                if not self.state.key_Pressed:
                    corner = (
                        self.state.stroke.min_corner,
                        self.state.stroke.max_corner,
                    )
                    # Get selected brush
                    self.state.stroke.select_guides = (
                        brush_utils.get_curves_within_surface_radius(
                            self.state.all_guides, self.state.stroke.position, corner
                        )
                    )
                    if self.state.is_reflect:
                        corner = (
                            self.state.rStroke.min_corner,
                            self.state.rStroke.max_corner,
                        )
                        self.state.rStroke.select_guides = (
                            brush_utils.get_curves_within_surface_radius(
                                self.state.all_guides,
                                self.state.rStroke.position,
                                corner,
                            )
                        )
                else:
                    self.state.stroke.select_guides = []
                    self.state.rStroke.select_guides = []

        elif self.state.type == BrushType.SCREEN:
            # Get origin of brush
            if not self.state.stroke.firstScale:
                self.state.stroke.origin = (
                    self.state.stroke.firstX,
                    self.state.stroke.firstY,
                )
            else:
                self.state.stroke.origin = (_position.x(), _position.y())

            # Update stroke direction
            if not self.state.stroke.lastPosition:
                self.state.stroke.lastPosition = (_position.x(), _position.y(), 0.0)
            else:
                pos = om.MPoint(_position.x(), _position.y(), 0.0)
                lastPos = om.MPoint(
                    self.state.stroke.lastPosition[0],
                    self.state.stroke.lastPosition[1],
                    0.0,
                )

                window_utils.view_to_world(pos)
                stroke_direction = pos - lastPos

                # stablize by taking only vectors with a certain length
                if stroke_direction.length() >= self.state.stroke.radius:
                    self.state.stroke.strokeDir = (
                        stroke_direction[0],
                        stroke_direction[1],
                        0.0,
                    )
                    self.state.stroke.lastPosition = (_position.x(), _position.y(), 0.0)

            # If there is any key pressed, do not operate guides anymore
            if not self.state.key_Pressed:
                if not self.state.dragged:
                    # Get selected curves and cvs
                    cvs_result = brush_utils.get_cvs_within_screen_radius(
                        self.state.all_guides,
                        self.state.stroke.position,
                        (self.state.stroke.cursorX, self.state.stroke.cursorY),
                        self.state.stroke.isHit,
                        self.state.stroke.radius,
                    )
                    (
                        self.state.stroke.select_cvs_idx,
                        self.state.stroke.select_guides,
                    ) = cvs_result
            else:
                del self.state.stroke.select_cvs_idx[:]

        if self.canvas:
            self.canvas.update()

    def update_stroke(self, stroke, cur_pos):
        """
        Update the stroke diection based on current and last mouse position
        """
        if not stroke.lastPosition:
            stroke.lastPosition = cur_pos
        else:
            pos = om.MPoint(cur_pos[0], cur_pos[1], cur_pos[2])
            last_pos = om.MPoint(
                stroke.lastPosition[0], stroke.lastPosition[1], stroke.lastPosition[2]
            )
            stroke_direction = pos - last_pos

            # stabilize by taking only vectors with a certain length
            if stroke_direction.length() >= stroke.radius * 0.1:
                stroke.strokeDir = (
                    stroke_direction[0],
                    stroke_direction[1],
                    stroke_direction[2],
                )
                stroke.lastPosition = cur_pos

    def clicked(self, position):
        # Open undo chunk to put those brush operations into one chunk
        # Close undo chun when mouse released
        isUndoOpen = cmds.undoInfo(q=True, state=True)
        if isUndoOpen:
            cmds.undoInfo(openChunk=True, chunkName="brushChunk")
        self.state.dragged = True
        # Clear stroke direction to prevent last stroke affecting current one
        if self.state.draw and self.state.mode:
            self.state.stroke.strokeDir = (0.0, 0.0, 0.0)
        if self.state.is_reflect:
            self.state.rStroke.strokeDir = (0.0, 0.0, 0.0)

        if self.state.type == BrushType.SCREEN and not self.state.key_Pressed:
            # Each time mouse clicked, update lock_length attribute for every curve
            if self.state.mode == BrushMode.SCULPT:
                CurveUtils.curves_lock_length_attr(
                    self.state.stroke.select_guides, self.state.lock_length
                )

    def dragged(self, position):
        if self.state.draw:
            if self.state.stroke.modifyRadius:
                if self.state.stroke.firstScale:
                    self.state.stroke.firstX = position.x()
                    self.state.stroke.firstY = position.y()
                    self.state.stroke.lastX = position.x()
                    self.state.stroke.lastY = position.y()
                    self.state.stroke.firstScale = False

                self.modifyRadius()
                self.state.stroke.lastX = position.x()
                self.state.stroke.lastY = position.y()

            else:
                if self.current_brush:
                    self.current_brush.evaluate(self.state)
                    self.view.refresh()

    def released(self, position):
        isUndoOpen = cmds.undoInfo(q=True, state=True)
        if isUndoOpen:
            cmds.undoInfo(closeChunk=True)
        self.state.dragged = False
        pass

    def enter(self):
        self.state.draw = True
        if self.canvas:
            self.canvas.update()

    def leave(self):
        self.state.draw = False
        if self.canvas:
            self.canvas.update()

    def bPressed(self):
        self.state.stroke.modifyRadius = True

    def bReleased(self):
        self.state.stroke.modifyRadius = False
        self.state.stroke.firstScale = True

    def keyPress(self):
        self.state.key_Pressed = True

    def keyRelease(self):
        self.state.key_Pressed = False

    def modifyRadius(self):
        """
        Modify the brush radius
        """
        deltaX = self.state.stroke.lastX - self.state.stroke.cursorX

        view = window_utils.activeView()
        camDag = OpenMaya.MDagPath()
        view.getCamera(camDag)
        camNodeFn = node_utils.getDgfnFromDagpath(camDag.fullPathName())
        camCoi = camNodeFn.findPlug("centerOfInterest").asDouble()

        step = deltaX * (camCoi * -0.001)
        if (self.state.stroke.radius + step) >= 0.01:
            self.state.stroke.radius += step
        else:
            self.state.stroke.radius = 0.01

    def set_current_brush(self, _current_brush):
        """
        Set current brush
        Register custom brush mode here
        """
        if _current_brush == BrushMode.LENGTH:
            self.current_brush = brush.length_brush.LengthBrush()
        elif _current_brush == BrushMode.ORIENT:
            self.current_brush = brush.orient_brush.OrientBrush()
        elif _current_brush == BrushMode.SCULPT:
            self.current_brush = brush.sculpt_brush.SculptBrush()

        self.state.mode = self.current_brush.brush_mode
        self.state.type = self.current_brush.brush_type


class CurveBrushContextCmd(OpenMayaMPx.MPxContextCommand):

    getter_map = {
        OpenMaya.MSyntax.kDouble: "flagArgumentDouble",
        OpenMaya.MSyntax.kUnsigned: "flagArgumentInt",
        OpenMaya.MSyntax.kBoolean: "flagArgumentBool",
        OpenMaya.MSyntax.kString: "flagArgumentString",
    }

    flags_data = {
        "-r": {"long": "-radius", "type": OpenMaya.MSyntax.kDouble},
        "-s": {"long": "-strength", "type": OpenMaya.MSyntax.kDouble},
        "-scs": {"long": "-sculptStrength", "type": OpenMaya.MSyntax.kDouble},
        "-cb": {"long": "-currentBrush", "type": OpenMaya.MSyntax.kUnsigned},
        "-ss": {"long": "-symmetrySetting", "type": OpenMaya.MSyntax.kUnsigned},
        "-lx": {"long": "-lockX", "type": OpenMaya.MSyntax.kBoolean},
        "-ly": {"long": "-lockY", "type": OpenMaya.MSyntax.kBoolean},
        "-lz": {"long": "-lockZ", "type": OpenMaya.MSyntax.kBoolean},
        "-ll": {"long": "-lockLength", "type": OpenMaya.MSyntax.kBoolean},
        "-im": {"long": "-inMesh", "type": OpenMaya.MSyntax.kString},
        "-cl": {"long": "-controlLength", "type": OpenMaya.MSyntax.kDouble},
    }

    def __new__(cls, *args, **kwargs):
        # NOTES(timmyliang): setup edit and query callback
        for name, func in inspect.getmembers(cls, inspect.ismethod):
            if name.startswith(("edit_", "query_")):
                key, flag = name.split("_")
                cls.flags_data["-{0}".format(flag)][key] = func

        return super(CurveBrushContextCmd, cls).__new__(cls, *args, **kwargs)

    def __init__(self):
        super(CurveBrushContextCmd, self).__init__()
        self.context = None

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
                getter = getattr(parser, self.getter_map.get(config.get("type")))
                value = getter(flag, 0)
                callback(self, value)

    def edit_r(self, value):
        self.context.state.stroke.radius = value
        self.context.canvas.update()

    def edit_s(self, value):
        self.context.state.stroke.strength = value

    def edit_scs(self, value):
        self.context.state.stroke.sculpt_strength = value

    def edit_cb(self, value):
        self.context.set_current_brush(value)

    def edit_ss(self, value):
        self.context.state.symmetry = value

    def edit_lx(self, value):
        self.context.state.lock_fur_scale_x = value

    def edit_ly(self, value):
        self.context.state.lock_fur_scale_y = value

    def edit_lz(self, value):
        self.context.state.lock_fur_scale_z = value

    def edit_im(self, value):
        self.context.state.mesh_str = value

    def edit_ll(self, value):
        self.context.state.lock_length = value

    def edit_cl(self, strength):
        if self.context:
            state = self.context.state
            attr_lock = (
                state.lock_fur_scale_x,
                state.lock_fur_scale_y,
                state.lock_fur_scale_z,
            )
            brush_utils.modifyCurveLength(
                state.stroke.select_guides, strength, attr_lock
            )
            self.context.canvas.update()
            self.context.view.refresh()

    def doQueryFlags(self):
        if not self.context:
            return

        parser = self._parser()  # type: OpenMaya.MArgParser
        for flag, config in self.flags_data.items():
            callback = config.get("query")
            if callable(callback) and parser.isFlagSet(flag):
                getter = getattr(parser, self.getter_map.get(config.get("type")))
                value = getter(flag, 0)
                callback(self, value)

    def query_r(self):
        self.setResult(self.context.state.stroke.radius)

    def query_s(self):
        self.setResult(self.context.state.stroke.strength)

    def query_scs(self):
        self.setResult(self.context.state.stroke.sculpt_strength)

    def query_ss(self):
        self.setResult(self.context.state.stroke.symmetry)

    def query_lx(self):
        self.setResult(self.context.state.stroke.lock_fur_scale_x)

    def query_ly(self):
        self.setResult(self.context.state.stroke.lock_fur_scale_y)

    def query_lz(self):
        self.setResult(self.context.state.stroke.lock_fur_scale_z)

    def query_im(self):
        self.setResult(self.context.state.stroke.mesh_str)

    def query_ll(self):
        self.setResult(self.context.state.stroke.lock_length)


@contextmanager
def try_run(name=""):
    if name:
        name = "py{0}".format(name)
    try:
        yield name
    except:
        if name:
            sys.stderr.write("Failed to register: %s\n" % name)
        raise


# Initialize the script plug-in
def initializePlugin(obj):

    plugin_fn = OpenMayaMPx.MFnPlugin(obj, "timmyliang", "1.0.0")
    path = plugin_fn.loadPath()
    print(path)

    with try_run(CurveBrushContextCmd.__name__) as name:
        plugin_fn.registerContextCommand(name, CurveBrushContextCmd.creator)


# Uninitialize the script plug-in
def uninitializePlugin(obj):
    plugin_fn = OpenMayaMPx.MFnPlugin(obj)

    with try_run(CurveBrushContextCmd.__name__) as name:
        plugin_fn.deregisterContextCommand(name)
