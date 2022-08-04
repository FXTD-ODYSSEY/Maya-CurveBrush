# -*- coding: utf-8 -*-
"""
setup Curve Brush Tool Properties.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2022-08-02 15:40:31"

from pymel.tools import py2mel
from pymel import core as pm


def curve_brush_properties():
    pm.setUITemplate("DefaultTemplate", pushTemplate=1)
    parent = str(pm.toolPropertyWindow(q=1, location=1))
    pm.setParent(parent)
    # curctx=str(currentCtx())
    pm.columnLayout("curveBrush")
    pm.tabLayout("curveBrushTabs", childResizable=True)
    pm.columnLayout("curveBrushTab")
    pm.frameLayout("curveBrushFrame", cll=True, l="curveBrush Options", cl=False)
    pm.columnLayout("curveBrushOptions")
    pm.separator(style="none")

    pm.intSliderGrp(
        "curveBrushStrength",
        field=1,
        minValue=20,
        maxValue=100,
        value=1,
        label="Brush Strength",
    )

    pm.intSliderGrp(
        "curveBrushRadius",
        field=1,
        minValue=20,
        maxValue=100,
        value=1,
        label="Brush Radius",
    )

    pm.setParent("..")
    pm.setParent("..")
    pm.setParent("..")
    pm.setParent("..")
    pm.setParent("..")
    # Name the tabs; -tl does not allow tab labelling upon creation
    pm.tabLayout("curveBrushTabs", tl=("curveBrushTab", "Tool Defaults"), e=1)
    pm.setUITemplate(popTemplate=1)
    curve_brush_callbacks(parent)


def curve_brush_callbacks(parent):

    pm.setParent(parent)
    whichCtx = str(pm.currentCtx())
    pm.intSliderGrp(
        "curveBrushStrength",
        e=1,
        cc=lambda *args: pm.curveBrushContext(whichCtx, strength=args[0], e=1),
    )
    pm.intSliderGrp(
        "curveBrushRadius",
        e=1,
        cc=lambda *args: pm.curveBrushContext(whichCtx, radius=args[0], e=1),
    )


def curve_brush_values(toolName):
    parent = (
        str(pm.toolPropertyWindow(q=1, location=1))
        + "|curveBrush|curveBrushTabs|curveBrushTab"
    )
    pm.setParent(parent)
    icon = "pythonFamily.png"
    pm.mel.toolPropertySetCommon(toolName, icon, "")
    pm.frameLayout("curveBrushFrame", en=True, e=1, cl=False)
    set_curve_brush_value(toolName)
    pm.mel.toolPropertySelect("curveBrush")


def set_curve_brush_value(toolName):
    pm.intSliderGrp(
        "curveBrushStrength", e=1, value=pm.curveBrushContext(toolName, q=1, strength=1)
    )
    pm.intSliderGrp(
        "curveBrushRadius", e=1, value=pm.curveBrushContext(toolName, q=1, radius=1)
    )

def setup_mel():
    py2mel.py2melProc(curve_brush_properties, procName="curveBrushProperties")
    py2mel.py2melProc(curve_brush_values, procName="curveBrushValues")
