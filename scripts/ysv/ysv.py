# Import future modules
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Import third-party modules
from maya.mel import eval
from pymel.core import *
import pymel.core.datatypes as dt
import pymel.core.nodetypes as nt
import pymel.core.uitypes as ui
import pymel.mayautils as mu


prefsFolderPath = mu.getMayaAppDir(1)


class PolyHistoryTypes:
    inComponents = [
        nt.PolyAppend,
        nt.PolyAverageVertex,
        nt.PolyBevel,
        nt.PolyBevel2,
        nt.PolyAutoProj,
        nt.PolyAverageVertex,
        nt.PolyBridgeEdge,
        nt.PolyChipOff,
        nt.PolyColorMod,
        nt.PolyColorPerVertex,
        nt.PolyConnectComponents,
        nt.PolyCut,
        nt.PolyCylProj,
        nt.PolyDelEdge,
        nt.PolyDuplicateEdge,
        nt.PolyEdgeToCurve,
        nt.PolyEditEdgeFlow,
        nt.PolyExtrudeEdge,
        nt.PolyExtrudeFace,
        nt.PolyExtrudeVertex,
        nt.PolyLayoutUV,
        nt.PolyMapSewMove,
        nt.PolyMergeEdge,
        nt.PolyMergeFace,
        nt.PolyMergeUV,
        nt.PolyMergeVert,
        nt.PolyMoveEdge,
        nt.PolyMoveFace,
        nt.PolyMoveFacetUV,
        nt.PolyMoveUV,
        nt.PolyMoveVertex,
        nt.PolyNormal,
        nt.PolyOptUvs,
        nt.PolyPlanarProj,
        nt.PolyProj,
        nt.PolyQuad,
        nt.PolyReduce,
        nt.PolySewEdge,
        nt.PolySmooth,
        nt.PolySmoothFace,
        nt.PolySmoothProxy,
        nt.PolySoftEdge,
        nt.PolySphProj,
        nt.PolySpinEdge,
        nt.PolySplit,
        nt.PolySplitRing,
        nt.PolyStraightenUVBorder,
        nt.PolySubdEdge,
        nt.PolySubdFace,
        nt.PolyTransfer,
        nt.PolyWedgeFace,
    ]

    solids = [
        nt.PolyCBoolOp,
        nt.PolyCone,
        nt.PolyCreateFace,
        nt.PolyCube,
        nt.PolyCylinder,
        nt.PolyHelix,
        nt.PolyPipe,
        nt.PolyPlane,
        nt.PolyPlatonicSolid,
        nt.PolyPrimitiveMisc,
        nt.PolyPrism,
        nt.PolyProjectCurve,
        nt.PolyPyramid,
        nt.PolySphere,
        nt.PolyToSubdiv,
        nt.PolyTorus,
    ]


def getCompLabel(iterType=MeshEdge):
    return getattr(iterType, "_ComponentLabel__")


def edgesIdsToStrList(i):
    return "e[{0}]".format(i)


def vertsIdsToStrList(i):
    return "vtx[{0}]".format(i)


def facesIdsToStrList(i):
    return "f[{0}]".format(i)


def idsToStr(inType):
    sel = ls(sl=1)
    ids = []

    if inType == MeshVertex:
        f = vertsIdsToStrList
    elif inType == MeshEdge:
        f = edgesIdsToStrList
    elif inType == MeshFace:
        f = facesIdsToStrList
    else:
        return

    for s in sel:
        if type(s) == inType:
            ids += s.indices()

    strL = list(map(f, ids))
    return strL




def fixPolyModifier(nextNode=None):
    if ls(sl=1, type=nt.PolyModifier) and not nextNode:
        node = ls(sl=1, type=nt.PolyModifier)[0]
        objMesh = ls(listFuture(node), et=nt.Mesh)[0]

        for n in listFuture(node):
            if type(n) == nt.Mesh:
                break
            setAttr(n.longName() + ".nodeState", 1)

        sel = [objMesh.longName() + "." + comp for comp in node.inputComponents.get()]

        setAttr(node.name() + ".nodeState", 1)
        hilite(objMesh)
        select(sel)
        return node

    if nextNode and not ls(sl=1, type=nt.PolyModifier) and not ls(sl=1, dag=1):
        node = nextNode
        objMesh = ls(listFuture(node), et=nt.Mesh)[0]
        sel = ls(sl=1)

        lastComp = ls(sel)[-1]
        attrValue = idsToStr(type(lastComp))

        cmd = "setAttr " + node.name() + ".inputComponents -type componentList "
        cmd += str(len(attrValue)) + " "
        for v in attrValue:
            cmd += v + " "

        eval(cmd)
        setAttr(node.longName() + ".nodeState", 0)

        nextN = listFuture(node)[1]

        if not type(nextN) == nt.Mesh:
            sel = []
            for comp in nextN.inputComponents.get():
                sel.append(objMesh.longName() + "." + comp)
        select(sel)

        return nextN


# ===============================================================================
# loc = mu.getMayaLocation().replace('\\', '/')
# print loc
# ===============================================================================
