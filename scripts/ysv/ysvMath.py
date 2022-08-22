# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import math

# Import third-party modules
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as mc
from maya.mel import eval as mEval
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt
import pymel.core.uitypes as ui
import pymel.mayautils as pu


def linePlaneIntersect(linePnt0, linePnt1, planePnt, planeNormal, epsilon=0.00001):
    lineNormal = linePnt1 - linePnt0
    w = linePnt0 - planePnt
    dot = planeNormal.dot(lineNormal)
    if abs(dot) > epsilon:
        factor = -planeNormal.dot(w) / dot
        return linePnt0 + (linePnt1 - linePnt0) * factor
    else:
        # The segment is parallel to plane
        return None
