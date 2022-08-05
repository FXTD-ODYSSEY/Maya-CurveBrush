# -*- coding: utf-8 -*-
"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2022-08-04 16:05:35"

from maya import cmds
import curve_brush_porperties
import os
import sys


def add_sys_path():
    root = cmds.moduleInfo(mn="CurveBrush", path=1)
    folders = ["Qt.py", "attrs/src"]
    for folder in folders:
        sys.path.append(os.path.join(root, "scripts", folder))


if not cmds.about(batch=1):
    add_sys_path()
    curve_brush_porperties.setup_mel()
