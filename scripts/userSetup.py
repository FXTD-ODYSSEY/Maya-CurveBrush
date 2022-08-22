# -*- coding: utf-8 -*-
"""

"""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import os
import sys

# Import third-party modules
import curve_brush_porperties
import pymel.core as pm
from importlib import import_module

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2022-08-04 16:05:35"


ysv_shelf_config = [
    {
        "command": lambda: (
            import_module("ysv.ysvPaintCurves").paintCtx("ysvCurveTweaker").run()
        ),
        "image": "insertKnot.png",
        "imageOverlayLabel": "ysv",
    },
    {
        "command": lambda: import_module("ysv.ysvPaintCurves").UI().create(),
        "image": "makeClip.png",
        "imageOverlayLabel": "UI",
    },
    {"command": "separator"},
    {
        "command": lambda: pm.setToolTo(pm.om1CurveBrushContext()),
        "image": "insertKnot.png",
        "imageOverlayLabel": "om1",
    },
    {
        "command": lambda: pm.setToolTo(pm.om2CurveBrushContext()),
        "image": "insertKnot.png",
        "imageOverlayLabel": "om2",
    },
    {
        "command": lambda: pm.setToolTo(pm.curveBrushContext()),
        "image": "insertKnot.png",
        "imageOverlayLabel": "cpp",
    },
]


def setup_ysv_tool(shelf_name="CurveBrush"):
    gShelfTopLevel = pm.melGlobals["gShelfTopLevel"]
    shelf_path = "|".join([gShelfTopLevel, shelf_name])

    # NOTES(timmyliang): delete old shelf
    if pm.shelfLayout(shelf_name, exists=1):
        pm.deleteUI(shelf_path, layout=1)

    pm.setParent(gShelfTopLevel)
    # NOTES(timmyliang): create a new shelf layout and select it
    layout = pm.shelfLayout(shelf_name)
    pm.shelfTabLayout(gShelfTopLevel, e=1, tabLabel=[layout, shelf_name])
    pm.tabLayout(gShelfTopLevel, e=1, selectTab=shelf_name)

    # NOTES(timmyliang): remove all child
    for child in pm.shelfLayout(shelf_path, q=1, ca=1) or []:
        pm.deleteUI(child)

    # NOTES(timmyliang): create a shelf button
    pm.setParent(shelf_path)

    for config in ysv_shelf_config:
        command = config.get("command", "")
        if command == "separator":
            pm.separator(
                style="shelf",
                horizontal=0,
                highlightColor=(0.321569, 0.521569, 0.65098),
                preventOverride=0,
                visible=1,
                enable=1,
                manage=1,
                enableBackground=0,
            )
        else:
            pm.shelfButton(
                command=command,
                image=config.get("image", "pythonFamily.png"),
                imageOverlayLabel=config.get("imageOverlayLabel", ""),
                sourceType="python",
            )


def add_sys_path():
    root = pm.moduleInfo(mn="CurveBrush", path=1)
    folders = ["Qt.py", "attrs/src"]
    for folder in folders:
        sys.path.append(os.path.join(root, "scripts", folder))


def main():
    add_sys_path()
    setup_ysv_tool()
    curve_brush_porperties.setup_mel()

    for plugin_name in ["om1_curve_brush.py", "om2_curve_brush.py", "curveBrush.mll"]:
        plugin_base = os.path.splitext(plugin_name)[0]
        if pm.pluginInfo(plugin_base, q=1, l=1):
            pm.unloadPlugin(plugin_base)
        pm.loadPlugin(plugin_name)


if not pm.about(batch=1):
    pm.evalDeferred(main, lp=1)
