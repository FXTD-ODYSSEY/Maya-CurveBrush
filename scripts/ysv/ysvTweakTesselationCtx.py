# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import importlib
import itertools as it
import math
import operator
import sys

# Import third-party modules
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as mc
from maya.mel import eval as mEval
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt

from . import ysvApiWrapers as ysvApi
from . import ysvCtx
from . import ysvMath
from . import ysvTransforms
from . import ysvUtils
from . import ysvView
from .ysvView import getInViewObjs


importlib.reload(ysvCtx)
baseDraggerCtx = ysvCtx.baseDraggerCtx


class ctx(baseDraggerCtx):
    def __init__(self, ctxName):
        baseDraggerCtx.__init__(self, ctxName)

        try:
            self.currentMesh = ls(sl=1, dag=1, et=nt.Mesh, ni=1)[0]
        except:
            self.currentMesh = None

        draggerContext(self.ctxName, e=1, cursor=ysvCtx.cursorType.hand)

    def selectPoly(self):
        inViewObjs = ysvView.getInViewObjs()
        meshes = ls(inViewObjs, dag=1, et=nt.Mesh, ni=1)
        if not meshes:
            return

        self.currentMesh = ysvView.closestMeshFromHit(
            meshes, self.cursorWPos, self.cursorWDir
        )

        if not self.currentMesh:
            select(cl=1)
            return

        select(self.currentMesh.getParent())

    def getClosestBoundaryInCurve(self):
        try:
            hist = listHistory(self.currentMesh)
            self.boundaryNode = ls(hist, et=nt.Boundary)[0]
            try:
                self.meshHit = ysvView.closestHitToMeshes(
                    [self.currentMesh.__apimfn__()], self.cursorWPos, self.cursorWDir
                )
            except:
                self.meshHit = None
                return

            inCurves = []
            try:
                self.inCurve1 = self.boundaryNode.inputCurve1.inputs(p=1)[0].node()
                if self.inCurve1:
                    d1 = self.inCurve1.distanceToPoint(self.meshHit, space="world")
                    inCurves.append((d1, self.inCurve1))
            except:
                pass
            try:
                self.inCurve2 = self.boundaryNode.inputCurve2.inputs(p=1)[0].node()
                if self.inCurve2:
                    d2 = self.inCurve2.distanceToPoint(self.meshHit, space="world")
                    inCurves.append((d2, self.inCurve2))
            except:
                pass

            try:
                self.inCurve3 = self.boundaryNode.inputCurve3.inputs(p=1)[0].node()
                if self.inCurve3:
                    d3 = self.inCurve3.distanceToPoint(self.meshHit, space="world")
                    inCurves.append((d3, self.inCurve3))
            except:
                pass

            try:
                self.inCurve4 = self.boundaryNode.inputCurve4.inputs(p=1)[0].node()
                if self.inCurve4:
                    d4 = self.inCurve4.distanceToPoint(self.meshHit, space="world")
                    inCurves.append((d4, self.inCurve4))
            except:
                pass

            self.closestCurve = min(inCurves, key=lambda x: x[0])[1]

            print(inCurves)

            if len(inCurves) == 4:
                if (
                    self.closestCurve == self.inCurve1
                    or self.closestCurve == self.inCurve3
                ):
                    self.direction = 1
                elif (
                    self.closestCurve == self.inCurve2
                    or self.closestCurve == self.inCurve4
                ):
                    self.direction = 2
            else:
                if (
                    self.closestCurve == self.inCurve1
                    or self.closestCurve == self.inCurve2
                ):
                    self.direction = 1
                elif self.closestCurve == self.inCurve3:
                    self.direction = 2

        except:
            pass

    def getTesselateNode(self):
        if not self.currentMesh:
            self.u = self.v = self.tessNode = None

        try:
            hist = listHistory(self.currentMesh)
            self.tessNode = ls(hist, et=nt.NurbsTessellate)[0]
            # print self.tessNode
            self.u = self.tessNode.uNumber
            self.v = self.tessNode.vNumber

            self.startUValue = self.u.get()
            self.startVValue = self.v.get()
        except:
            self.u = self.v = self.tessNode = None

    def noModsLMBOnPress(self):
        self.selectPoly()
        self.getTesselateNode()

    def shiftLMBOnPress(self):
        pass

    def ctrlLMBOnPress(self):
        pass

    def ctrlShiftLMBOnPress(self):
        pass

    def ctrlAltShiftLMBOnPress(self):
        pass

    def noModsLMBOnDrag(self):
        self.selectPoly()
        self.getClosestBoundaryInCurve()

    def shiftLMBOnDrag(self):
        pass

    def ctrlLMBOnDrag(self):
        pass

    def ctrlShiftLMBOnDrag(self):
        pass

    def ctrlAltShiftLMBOnDrag(self):
        pass

    def noModsLMBOnRelease(self):
        pass

    def shiftLMBOnRelease(self):
        pass

    def ctrlLMBOnRelease(self):
        pass

    def ctrlShiftLMBOnRelease(self):
        pass

    def ctrlAltShiftLMBOnRelease(self):
        pass

    # -------------------------------------MMB-----------------------------------
    def MMBOnPress(self):
        self.selectPoly()
        draggerContext(self.ctxName, e=1, cursor="crossHair")
        self.getTesselateNode()

        self.direction = None

    def noModsMMBOnPress(self):
        self.MMBOnPress()

    def shiftMMBOnPress(self):
        self.MMBOnPress()

    def ctrlMMBOnPress(self):
        self.MMBOnPress()

    def ctrlShiftMMBOnPress(self):
        self.MMBOnPress()

    def ctrlAltShiftMMBOnPress(self):
        self.MMBOnPress()

    def MMBOnDrag(self, mult=0.02):
        draggerContext(self.ctxName, e=1, cursor="crossHair")

        if not self.direction:
            self.getClosestBoundaryInCurve()

        if abs(self.cursorDeltaX) > abs(self.cursorDeltaY):
            offset = self.cursorDeltaX
        elif abs(self.cursorDeltaY) > abs(self.cursorDeltaX):
            offset = self.cursorDeltaY

        # offset = dt.Vector(self.cursorDeltaX, self.cursorDeltaY, 0).length()
        # if self.cursorDeltaX<0 or self.cursorDeltaY<0:
        #    offset = -offset

        if not self.direction:
            if max(abs(self.cursorDeltaX), abs(self.cursorDeltaY)) > 50:
                if abs(self.cursorDeltaX) >= abs(self.cursorDeltaY):
                    self.direction = 1
                else:
                    self.direction = 2
            self.dirByScreenDir = True
        else:
            # print 'finded dir by curve'
            self.dirByScreenDir = False

        if self.direction == 1:
            try:
                if self.dirByScreenDir:
                    value = self.startUValue + self.cursorDeltaX * mult
                else:
                    value = self.startUValue + offset * mult

                self.u.set(value)
            except:
                pass

        elif self.direction == 2:
            try:
                if self.dirByScreenDir:
                    value = self.startVValue + self.cursorDeltaY * mult
                else:
                    value = self.startVValue + offset * mult

                self.v.set(value)
            except:
                pass

        try:
            inViewMessage(msg=int(value), pos="midCenterTop", dk=1)
        except:
            pass

        self.activeView.refresh()

    def noModsMMBOnDrag(self):
        self.MMBOnDrag(mult=0.05)

    def shiftMMBOnDrag(self):
        self.MMBOnDrag(mult=0.1)

    def ctrlMMBOnDrag(self):
        self.MMBOnDrag(mult=0.02)

    def ctrlShiftMMBOnDrag(self):
        self.MMBOnDrag(mult=0.5)

    def ctrlAltShiftMMBOnDrag(self):
        self.MMBOnDrag(mult=1.0)

    def noModsMMBOnRelease(self):
        pass

    def shiftMMBOnRelease(self):
        pass

    def ctrlMMBOnRelease(self):
        pass

    def ctrlShiftMMBOnRelease(self):
        pass

    def ctrlAltShiftMMBOnRelease(self):
        pass

    def prePress(self):
        baseDraggerCtx.prePress(self)

    def onPress(self):
        # print 'currentMesh : ', self.currentMesh
        baseDraggerCtx.onPress(self)

    def onDrag(self):
        baseDraggerCtx.onDrag(self)

    def onRelease(self):
        baseDraggerCtx.onRelease(self)
        draggerContext(self.ctxName, e=1, cursor=ysvCtx.cursorType.hand)

    def run(self):
        baseDraggerCtx.run(self)

    def finalize(self):
        baseDraggerCtx.finalize(self)


# ctx('ysvTweakTesselationCtx').run()
