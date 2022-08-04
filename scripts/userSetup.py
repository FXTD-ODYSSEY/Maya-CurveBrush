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

if not cmds.about(batch=1):
    curve_brush_porperties.setup_mel()
