# -*- coding: utf-8 -*-
"""
Curve Brush Tweak curve.
ctx = cmds.squareScaleManipContext()
cmds.setToolTo(ctx)
"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
from contextlib import contextmanager
import logging
import math
import sys

# Import third-party modules
import _curve_brush
import attr
from maya.api import OpenMaya
from maya.api import OpenMayaRender
from maya.api import OpenMayaUI
from pymel import core as pm


logger = logging.getLogger("SquareScaleManipContext")

# tell Maya that we want to use Python API 2.0
maya_useNewAPI = True


class CurveBrushManipulator(OpenMayaUI.MPxManipulatorNode):
    kTypeId = OpenMaya.MTypeId(0x81148)

    def __init__(self):
        """
        Initialize the manipulator member variables.
        """
        super(CurveBrushManipulator, self).__init__()

        # # Setup the plane with a point on the plane along with a normal
        # self.point_on_plane = SquareGeometry.top_left()

        # # Set plug indicies to a default
        # self.top_index = -1
        # self.right_index = -1
        # self.bottom_index = -1
        # self.left_index = -1
        # self.top_name = -1
        # self.right_name = -1
        # self.bottom_name = -1
        # self.left_name = -1

        # # initialize rotate/translate to a good default
        # self.rotate_x = 0.0
        # self.rotate_y = 0.0
        # self.rotate_z = 0.0
        # self.translate_x = 0.0
        # self.translate_y = 0.0
        # self.translate_z = 0.0

        # # Normal = cross product of two vectors on the plane
        # v1 = OpenMaya.MVector(SquareGeometry.top_left()) - OpenMaya.MVector(
        #     SquareGeometry.top_right()
        # )
        # v2 = OpenMaya.MVector(SquareGeometry.top_right()) - OpenMaya.MVector(
        #     SquareGeometry.bottom_right()
        # )
        # self.normal_to_plane = v1 ^ v2

        # # Necessary to normalize
        # self.normal_to_plane.normalize()
        # self.plane = PlaneMath()
        # self.plane.set_plane(self.point_on_plane, self.normal_to_plane)

    @classmethod
    def creator(cls):
        return cls()

    @classmethod
    def initialize(cls):
        pass

    # virtual
    def postConstructor(self):
        self.top_index = self.addDoubleValue("topValue", 0)
        self.right_index = self.addDoubleValue("rightValue", 0)
        self.bottom_index = self.addDoubleValue("bottomValue", 0)
        self.left_index = self.addDoubleValue("leftValue", 0)

        gl_pickable_item = self.glFirstHandle()
        self.top_name = gl_pickable_item
        self.bottom_name = gl_pickable_item + 1
        self.right_name = gl_pickable_item + 2
        self.left_name = gl_pickable_item + 3

    # virtual
    def connectToDependNode(self, depend_node):
        """
        Connect the manipulator to the given dependency node.
        """

        # Make sure we have a scaleX plug and connect the
        # plug to the rightIndex we created in the postConstructor
        scale_x_plug = None
        nodeFn = OpenMaya.MFnDependencyNode(depend_node)

        try:
            scale_x_plug = nodeFn.findPlug("scaleX", True)
        except:
            logger.info("    Could not find scaleX plug!")
            return

        plug_index = 0
        try:
            plug_index = self.connectPlugToValue(scale_x_plug, self.right_index)
        except:
            logger.info("    Could not connectPlugToValue!")
            return

        self.finishAddingManips()
        return OpenMayaUI.MPxManipulatorNode.connectToDependNode(self, depend_node)

    def pre_draw(self):
        """
        Update the region dragged by the mouse.
        """

        # Populate the point arrays which are in local space
        tl = SquareGeometry.top_left()
        tr = SquareGeometry.top_right()
        bl = SquareGeometry.bottom_left()
        br = SquareGeometry.bottom_right()

        # Depending on what's active, we modify the
        # end points with mouse deltas in local space
        active = self.glActiveName()
        if active:
            if active == self.top_name:
                tl += self.mouse_point_gl_name
                tr += self.mouse_point_gl_name
            if active == self.bottom_name:
                bl += self.mouse_point_gl_name
                br += self.mouse_point_gl_name
            if active == self.right_name:
                tr += self.mouse_point_gl_name
                br += self.mouse_point_gl_name
            if active == self.left_name:
                tl += self.mouse_point_gl_name
                bl += self.mouse_point_gl_name

        return [tl, tr, bl, br]

    # virtual
    def preDrawUI(self, view):
        """
        Cache the viewport for use in VP 2.0 drawing.
        """
        pass

    # virtual
    def drawUI(self, draw_manager, frame_context):
        """
        Draw the manupulator in a VP 2.0 viewport.
        """

        [tl, tr, bl, br] = self.pre_draw()

        xform = OpenMaya.MTransformationMatrix()
        xform.rotateByComponents(
            [
                math.degrees(self.rotate_x),
                math.degrees(self.rotate_y),
                math.degrees(self.rotate_z),
                OpenMaya.MTransformationMatrix.kZYX,
            ],
            OpenMaya.MSpace.kWorld,
        )

        mat = xform.asMatrix()
        tl *= mat
        tr *= mat
        bl *= mat
        br *= mat

        # Top
        draw_manager.beginDrawable(
            OpenMayaRender.MUIDrawManager.kNonSelectable, self.top_name
        )
        self.setHandleColor(draw_manager, self.top_name, self.dimmedColor())
        draw_manager.line(tl, tr)
        draw_manager.endDrawable()

        # Right
        draw_manager.beginDrawable(
            OpenMayaRender.MUIDrawManager.kSelectable, self.right_name
        )
        self.setHandleColor(draw_manager, self.right_name, self.mainColor())
        draw_manager.line(tr, br)
        draw_manager.endDrawable()

        # Bottom
        draw_manager.beginDrawable(
            OpenMayaRender.MUIDrawManager.kNonSelectable, self.bottom_name
        )
        self.setHandleColor(draw_manager, self.bottom_name, self.dimmedColor())
        draw_manager.line(br, bl)
        draw_manager.endDrawable()

        # Left
        draw_manager.beginDrawable(
            OpenMayaRender.MUIDrawManager.kSelectable, self.left_name
        )
        self.setHandleColor(draw_manager, self.left_name, self.mainColor())
        draw_manager.line(bl, tl)
        draw_manager.endDrawable()

    # virtual
    def doPress(self, view):
        """
        Handle the mouse press event in a VP2.0 viewport.
        """
        # Reset the mousePoint information on a new press.
        self.mouse_point_gl_name = OpenMaya.MPoint.kOrigin
        self.update_drag_information()

    # virtual
    def doDrag(self, view):
        """
        Handle the mouse drag event in a VP2.0 viewport.
        """
        self.update_drag_information()

    # virtual
    def doRelease(self, view):
        """
        Handle the mouse release event in a VP2.0 viewport.
        """
        pass

    def set_draw_transform_info(self, rotation, translation):
        """
        Store the given rotation and translation.
        """
        self.rotate_x = rotation[0]
        self.rotate_y = rotation[1]
        self.rotate_z = rotation[2]
        self.translate_x = translation[0]
        self.translate_y = translation[1]
        self.translate_z = translation[2]

    def update_drag_information(self):
        """
        Update the mouse's intersection location with the manipulator
        """
        # Find the mouse point in local space
        self.local_mouse = self.mouseRay()

        # Find the intersection of the mouse point with the manip plane
        mouse_intersection_with_manip_plane = self.plane.intersect(self.local_mouse)

        self.mouse_point_gl_name = mouse_intersection_with_manip_plane

        active = self.glActiveName()
        if active:
            start = OpenMaya.MPoint([0, 0, 0])
            end = OpenMaya.MPoint([0, 0, 0])
            if active == self.top_name:
                start = OpenMaya.MPoint(-0.5, 0.5, 0.0)
                end = OpenMaya.MPoint(0.5, 0.5, 0.0)
            if active == self.bottom_name:
                start = OpenMaya.MPoint(-0.5, -0.5, 0.0)
                end = OpenMaya.MPoint(0.5, -0.5, 0.0)
            if active == self.right_name:
                start = OpenMaya.MPoint(0.5, 0.5, 0.0)
                end = OpenMaya.MPoint(0.5, -0.5, 0.0)
            if active == self.left_name:
                start = OpenMaya.MPoint(-0.5, 0.5, 0.0)
                end = OpenMaya.MPoint(-0.5, -0.5, 0.0)

            if active:
                # Find a vector on the plane
                a = OpenMaya.MPoint(start.x, start.y, start.z)
                b = OpenMaya.MPoint(end.x, end.y, end.z)
                vab = a - b

                # Define line with a point and a vector on the plane
                line = LineMath()
                line.set_line(start, vab)

                # Find the closest point so that we can get the
                # delta change of the mouse in local space
                cpt = line.closest_point(self.mouse_point_gl_name)
                self.mouse_point_gl_name -= cpt

                min_change_value = min(
                    self.mouse_point_gl_name.x,
                    self.mouse_point_gl_name.y,
                    self.mouse_point_gl_name.z,
                )
                max_change_value = max(
                    self.mouse_point_gl_name.x,
                    self.mouse_point_gl_name.y,
                    self.mouse_point_gl_name.z,
                )
                if active == self.right_name:
                    self.setDoubleValue(self.right_index, max_change_value)
                if active == self.left_name:
                    self.setDoubleValue(self.right_index, min_change_value)


# command
class CruveBrushManipContextCmd(OpenMayaUI.MPxContextCommand):
    """
    This command class is used to create instances of the SquareScaleManipContext class.
    """

    kPluginCmdName = "squareScaleManipContext"

    def __init__(self):
        OpenMayaUI.MPxContextCommand.__init__(self)

    @staticmethod
    def creator():
        return CruveBrushManipContextCmd()

    def makeObj(self):
        """
        Create and return an instance of the SquareScaleManipContext class.
        """
        return CurveBrushManipContext()


class CurveBrushManipContext(OpenMayaUI.MPxSelectionContext):
    """
    This context handles all mouse interaction in the viewport when activated.
        When activated, it creates and manages an instance of the SquareScaleManuplator
    class on the selected objects.
    """

    kContextName = "SquareScaleManipContext"

    @classmethod
    def creator(cls):
        return cls()

    def __init__(self):
        """
        Initialize the members of the SquareScaleManipContext class.
        """
        OpenMayaUI.MPxSelectionContext.__init__(self)
        self.setTitleString(
            "Plug-in manipulator: " + CurveBrushManipContext.kContextName
        )
        self.manipulator_class_ptr = None
        self.first_object_selected = None
        self.active_list_modified_msg_id = -1

    # virtual
    def toolOnSetup(self, event):
        """
        Set the help string and selection list callback.
        """
        self.setHelpString("Move the object using the manipulator")

        CurveBrushManipContext.update_manipulators_cb(self)
        try:
            self.active_list_modified_msg_id = OpenMaya.MModelMessage.addCallback(
                OpenMaya.MModelMessage.kActiveListModified,
                CurveBrushManipContext.update_manipulators_cb,
                self,
            )
        except:
            OpenMaya.MGlobal.displayError(
                "SquareScaleManipContext.toolOnSetup(): Model addCallback failed"
            )

    # Removes the callback
    # virtual
    def toolOffCleanup(self):
        """
        Unregister the selection list callback.
        """
        try:
            OpenMaya.MModelMessage.removeCallback(self.active_list_modified_msg_id)
            self.active_list_modified_msg_id = -1
        except:
            OpenMaya.MGlobal.displayError(
                "SquareScaleManipContext.toolOffCleanup(): Model remove callback failed"
            )

        OpenMayaUI.MPxSelectionContext.toolOffCleanup(self)

    # virtual
    def namesOfAttributes(self, attribute_names):
        """
        Return the names of the attributes of the selected objects this context will be modifying.
        """
        attribute_names.append("scaleX")

    # virtual
    def setInitialState(self):
        """
        Set the initial transform of the manipulator.
        """
        xform = OpenMaya.MFnTransform(self.first_object_selected)
        xformMatrix = xform.transformation()
        translation = xformMatrix.translation(OpenMaya.MSpace.kWorld)
        rotation = xformMatrix.rotation(False)

        self.manipulator_class_ptr.set_draw_transform_info(rotation, translation)

    # Ensure that valid geometry is selected
    def valid_geometry_selected(self):
        """
        Check to make sure the selected objects have transforms.
        """
        list = None
        iter = None
        try:
            list = OpenMaya.MGlobal.getActiveSelectionList()
            iter = OpenMaya.MItSelectionList(list)
        except:
            logger.info("    Could not get active selection")
            return False

        if (not list) or (list.length() == 0):
            return False

        while not iter.isDone():
            depend_node = iter.getDependNode()
            if depend_node.isNull() or (not depend_node.hasFn(OpenMaya.MFn.kTransform)):
                OpenMaya.MGlobal.displayWarning(
                    "Object in selection list is not right type of node"
                )
                return False
            iter.next()
        return True

    @staticmethod
    def update_manipulators_cb(ctx):
        """
        Callback that creates the manipulator if valid geometry is selected. Also removes
        the manipulator if no geometry is selected. Handles connecting the manipulator to
        multiply selected nodes.
        """
        try:
            ctx.deleteManipulators()
        except:
            logger.info("    No manipulators to delete")

        try:
            if not ctx.valid_geometry_selected():
                return

            # Clear info
            ctx.manipulator_class_ptr = None
            ctx.first_object_selected = OpenMaya.MObject.kNullObj

            (manipulator, manip_object) = CurveBrushManipulator.newManipulator(
                "SquareScaleContextManipulator"
            )

            if manipulator:
                # Save state
                ctx.manipulator_class_ptr = manipulator

                # Add the manipulator
                ctx.addManipulator(manip_object)

                list = OpenMaya.MGlobal.getActiveSelectionList()
                iter = OpenMaya.MItSelectionList(list)

                while not iter.isDone():
                    depend_node = iter.getDependNode()
                    depend_node_fn = OpenMaya.MFnDependencyNode(depend_node)

                    # Connect the manipulator to the object in the selection list.
                    if not manipulator.connectToDependNode(depend_node):
                        OpenMaya.MGlobal.displayWarning(
                            "Error connecting manipulator to object %s"
                            % depend_node_fn.name()
                        )
                        iter.next()
                        continue

                    if ctx.first_object_selected == OpenMaya.MObject.kNullObj:
                        ctx.first_object_selected = depend_node
                    iter.next()

                # Allow the manipulator to set initial state
                ctx.setInitialState()

        except:
            OpenMaya.MGlobal.displayError("Failed to create new manipulator")
            return


@contextmanager
def try_run(name=""):
    try:
        yield
    except:
        if name:
            sys.stderr.write("Failed to register: %s\n" % name)
        raise


# Initialize the script plug-in
def initializePlugin(plugin):
    pluginFn = OpenMaya.MFnPlugin(plugin)

    with try_run(CruveBrushManipContextCmd.kPluginCmdName):
        pluginFn.registerContextCommand(
            CruveBrushManipContextCmd.kPluginCmdName, CruveBrushManipContextCmd.creator
        )

    with try_run(CurveBrushManipulator.__name__):
        pluginFn.registerNode(
            CurveBrushManipulator.__name__,
            CurveBrushManipulator.kTypeId,
            CurveBrushManipulator.creator,
            CurveBrushManipulator.initialize,
            OpenMaya.MPxNode.kManipulatorNode,
        )


# Uninitialize the script plug-in
def uninitializePlugin(plugin):
    pluginFn = OpenMaya.MFnPlugin(plugin)

    with try_run(CruveBrushManipContextCmd.kPluginCmdName):
        pluginFn.deregisterContextCommand(CruveBrushManipContextCmd.kPluginCmdName)

    with try_run(CurveBrushManipulator.__name__):
        pluginFn.deregisterNode(CurveBrushManipulator.kTypeId)
