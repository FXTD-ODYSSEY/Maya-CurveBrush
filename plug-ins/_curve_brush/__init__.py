# -*- coding: utf-8 -*-
"""Curve Brush Plugin Utility Library."""

# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import built-in modules
import sys
import os

try:
    import Qt
    import six
    import attr
except ImportError:
    DIR = os.path.dirname(__file__)
    MODULE = os.path.join(DIR, "_vendor")
    if MODULE not in sys.path:
        sys.path.insert(0, MODULE)
    import Qt
    import six
    import attr
