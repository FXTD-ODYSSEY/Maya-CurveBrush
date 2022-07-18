import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from maya.mel import eval as mEval
import maya.cmds as mc
from pymel.core import *
import pymel.core.uitypes as ui
import pymel.core.nodetypes as nt
import pymel.core.datatypes as dt
import pymel.mayautils as pu

import math

def linePlaneIntersect(linePnt0, linePnt1, planePnt, planeNormal, epsilon=0.00001):
    lineNormal = linePnt1 - linePnt0
    w = linePnt0 - planePnt
    dot = planeNormal.dot(lineNormal)
    if abs(dot) > epsilon:
        factor = -planeNormal.dot(w)/dot
        return linePnt0 + (linePnt1-linePnt0)*factor
    else:
        # The segment is parallel to plane
        return None